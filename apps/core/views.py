from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from apps.blog.models import Post  # On garde le blog pour le contenu éditorial
from .forms import ContactForm

class HomePageView(TemplateView):
    template_name = "core/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Afficher les 3 derniers articles du blog (pour la crédibilité et le SEO)
        context['latest_posts'] = Post.objects.filter(
            status='published'
        ).select_related('author').order_by('-published_at')[:3]
        
        # Ici tu pourras ajouter plus tard :
        # context['featured_profiles'] = Profile.objects.filter(is_featured=True)
        
        return context

class AboutPageView(TemplateView):
    template_name = "core/about.html"

class ContactPageView(CreateView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy('core:contact')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Votre message a été envoyé avec succès !")
        return super().form_valid(form)