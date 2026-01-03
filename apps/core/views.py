from django.views.generic import TemplateView
from apps.blog.models import Post
from apps.portfolio.models import Project
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import ContactForm

class HomePageView(TemplateView):
    template_name = "core/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Les 3 derniers articles de blog (Triés par date de publication)
        context['latest_posts'] = Post.objects.filter(
            status='published'
        ).select_related('author').order_by('-published_at')[:3]
        
        # 2. Les 3 projets mis en avant (ou les 3 plus récents)
        # On utilise select_related pour la catégorie afin d'optimiser les requêtes SQL
        context['featured_projects'] = Project.objects.filter(
            is_published=True,
            is_featured=True  # Assure-toi de cocher cette case dans l'admin
        ).select_related('category').prefetch_related('technologies').order_by('order')[:3]
        
        return context

class AboutPageView(TemplateView):
    template_name = "core/about.html"


class ContactPageView(CreateView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy('core:contact')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Votre message a été envoyé avec succès ! Je vous répondrai très prochainement.")
        return super().form_valid(form)
class ServicePageView(TemplateView):
    template_name = "core/services.html"
    
