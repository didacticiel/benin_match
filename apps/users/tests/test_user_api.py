# apps/users/tests/test_user_api.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

# Les URLs sont définies dans CvDidacticiel_API/urls.py et apps/users/urls.py
# Base : /api/v1/users/

class UserAuthenticationTests(APITestCase):
    
    def setUp(self):
        # Création d'un utilisateur de base pour les tests nécessitant une connexion
        self.user_data = {
            'email': 'testuser@email.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
        }
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            username=self.user_data['email'] # Utilisé comme username
        )
        
        # URLs de l'API
        self.register_url = '/api/v1/users/register/' # Directement dans apps.users.urls
        self.login_url = '/api/v1/auth/login/'        # Dans le routing principal
        self.logout_url = '/api/v1/auth/logout/'      # Dans le routing principal
        self.me_url = '/api/v1/users/me/'             # Directement dans apps.users.urls

    # ----------------------------------------------------------------------
    # TEST 1 : ENREGISTREMENT (REGISTER)
    # ----------------------------------------------------------------------
    def test_user_registration_success(self):
        """Test l'enregistrement d'un utilisateur avec succès."""
        new_data = {
            'email': 'newuser@email.com',
            'password': 'strongpassword',
            'password2': 'strongpassword',
            'first_name': 'Nouveau',
            'last_name': 'Compte',
        }
        response = self.client.post(self.register_url, new_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('access' in response.data) # Vérifie qu'un token est retourné
        self.assertTrue('refresh' in response.data)
        self.assertEqual(User.objects.count(), 2) # Vérifie que l'utilisateur a été créé

    def test_user_registration_password_mismatch(self):
        """Test l'échec de l'enregistrement si les mots de passe ne correspondent pas."""
        new_data = {
            'email': 'failuser@email.com',
            'password': 'strongpassword',
            'password2': 'wrongpassword', # Mismatch
            'first_name': 'Fail',
            'last_name': 'Test',
        }
        response = self.client.post(self.register_url, new_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(User.objects.count(), 1) # Vérifie qu'aucun utilisateur n'a été créé

    # ----------------------------------------------------------------------
    # TEST 2 : CONNEXION (LOGIN - Obtention de Tokens JWT)
    # ----------------------------------------------------------------------
    def test_user_login_success(self):
        """Test la connexion d'un utilisateur avec succès et obtention des tokens."""
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('access' in response.data)
        self.assertTrue('refresh' in response.data)

    def test_user_login_failure(self):
        """Test l'échec de la connexion avec un mauvais mot de passe."""
        login_data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    # ----------------------------------------------------------------------
    # TEST 3 : PROFIL (GET /me/)
    # ----------------------------------------------------------------------
    def test_get_user_profile_authenticated(self):
        """Test l'accès au profil (/me/) pour un utilisateur authentifié."""
        # Obtient les tokens d'abord
        login_data = {'email': self.user_data['email'], 'password': self.user_data['password']}
        login_response = self.client.post(self.login_url, login_data, format='json')
        access_token = login_response.data['access']
        
        # Configure l'en-tête d'authentification (Bearer Token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        
        response = self.client.get(self.me_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])
        self.assertFalse(response.data['is_premium_subscriber'])
        self.assertTrue('password' not in response.data) # Sécurité

    def test_get_user_profile_unauthenticated(self):
        """Test l'échec de l'accès au profil (/me/) sans authentification."""
        response = self.client.get(self.me_url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ----------------------------------------------------------------------
    # TEST 4 : DÉCONNEXION (LOGOUT)
    # ----------------------------------------------------------------------
    def test_user_logout_success(self):
        """Test la déconnexion réussie (Blacklist du Refresh Token)."""
        # 1. Login pour obtenir le refresh token
        login_data = {'email': self.user_data['email'], 'password': self.user_data['password']}
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        access_token = login_response.data['access']

        # 2. Logout (nécessite l'access token dans l'en-tête et le refresh token dans le corps)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_response = self.client.post(self.logout_url, {'refresh': refresh_token}, format='json')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)


        # 3. Vérifier que l'Access Token est invalide après le logout (Optionnel: nécessite le rafraichissement)
        # On peut surtout vérifier que le refresh token est invalide:
        refresh_url = '/api/v1/auth/refresh/'
        refresh_check = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        
        self.assertEqual(refresh_check.status_code, status.HTTP_401_UNAUTHORIZED)
        #self.assertIn('Token is blacklisted', str(refresh_check.data))
        self.assertIn('Le jeton a été banni', str(refresh_check.data))