from django.test import TestCase
from django.contrib.auth import get_user_model

class UsersManagersTests(TestCase):

    def test_create_user(self):
        """Logique : Créer un utilisateur avec email ET username obligatoires"""
        User = get_user_model()
        user = User.objects.create_user(
            email='normal@didacticiel.bj',
            username='abdoul_dev', # AJOUTÉ car requis par ton modèle
            password='foo',
            first_name='Abdoul',   # Recommandé car blank=False dans ton modèle
            last_name='Didacticiel'
        )
        self.assertEqual(user.email, 'normal@didacticiel.bj')
        self.assertEqual(user.username, 'abdoul_dev')
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        """Logique : Créer un admin avec les champs requis"""
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            email='super@didacticiel.bj',
            username='admin_didacticiel', # AJOUTÉ
            password='foo',
            first_name='Admin',
            last_name='User'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_user_password_hashing(self):
        User = get_user_model()
        user = User.objects.create_user(
            email='test@test.com', 
            username='testeur', 
            password='secret_password_123'
        )
        self.assertNotEqual(user.password, 'secret_password_123')
        self.assertTrue(user.check_password('secret_password_123'))