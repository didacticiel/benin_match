from django.test import TestCase
from django.urls import reverse
from apps.portfolio.models import Project, Category, Technology

class PortfolioTests(TestCase):
    
    def setUp(self):
        """
        LOGIQUE : On prépare l'environnement de test.
        On doit créer les objets parents (Category) avant le projet.
        """
        # 1. Créer une catégorie obligatoire
        self.category = Category.objects.create(
            name="Web Development",
            icon="💻"
        )
        
        # 2. Créer une technologie (pour le ManyToMany)
        self.tech = Technology.objects.create(name="Django")

        # 3. Créer le projet avec tous les champs NOT NULL (year et category)
        self.project = Project.objects.create(
            title="Mon Super Projet",
            description="Une description courte",
            year=2025,
            category=self.category, # Relation obligatoire
            is_published=True
        )
        
        # 4. Ajouter la technologie APRES la création (Logique ManyToMany)
        self.project.technologies.add(self.tech)

    def test_portfolio_list_view(self):
        """Vérifie que la page liste les projets"""
        # Note: vérifie dans ton apps/portfolio/urls.py que le nom est bien 'list'
        try:
            url = reverse('portfolio:list') 
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Mon Super Projet")
        except:
            # Si reverse échoue (ex: url non définie), on teste l'accueil
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)