from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings

from .forms import ContactForm
from .models import ContactMessage

class ContactView(FormView):
    """
    Page de contact.
    Envoi un email aux admins et sauvegarde le message en base de données.
    """
    template_name = "contact/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy('contact:success')

    def form_valid(self, form):
        # 1. Sauvegarder le message en base (pour l'historique admin)
        contact_message = form.save(commit=False)
        
        # 2. Envoi de l'Email réel
        subject = f"[Benin Match] Nouveau message de : {contact_message.full_name}"
        message_content = f"""
        De : {contact_message.full_name} ({contact_message.email})
        Sujet : {contact_message.subject}
        
        Message :
        {contact_message.message}
        """
        
        try:
            # Essai d'envoi (Si la config email est correcte)
            send_mail(
                subject,
                message_content,
                settings.DEFAULT_FROM_EMAIL, # L'expéditeur
                [settings.ADMIN_EMAIL],       # Le destinataire (ton admin)
                fail_silently=False,
            )
        except Exception as e:
            # En cas d'erreur SMTP (ex: pas de serveur mail de config)
            # On ne plante pas la page, on logue l'erreur
            print(f"Erreur lors de l'envoi email : {e}")

        # Sauvegarde en base après envoi (ou échec)
        contact_message.save()

        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Coordonnées du support (à remplacer par les tiennes)
        context['support_email'] = "hadaloudidacticiel@gmail.com"
        context['support_phone'] = "+229 01 40 44 55 41"
        context['support_address'] = "Cotonou, Bénin"
        return context