from django import forms
from .models import Profile, ProfileImage

class ProfileForm(forms.ModelForm):
    """
    Formulaire principal.
    Gère : Nom, Prénom (User) + Infos Profil (Profile) + AVATAR (User).
    """
    
    # --- CHAMPS HORS MODÈLE (User) ---
    first_name = forms.CharField(
        label="Prénom",
        required=True,
        widget=forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Votre prénom'})
    )
    last_name = forms.CharField(
        label="Nom",
        required=True,
        widget=forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Votre nom'})
    )
    
    # --- CHAMP MANUEL (Avatar User) ---
    avatar = forms.ImageField(
        label="Ma photo de profil",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/png, image/jpeg, image/webp'
        }),
        help_text="JPG ou PNG. Max 2MB. C'est la photo qui apparaîtra dans la grille."
    )

    class Meta:
        model = Profile
        fields = ['gender', 'date_of_birth', 'city', 'country', 'is_diaspora', 'relationship_goal', 'bio'] 
        
        widgets = {
            'gender': forms.Select(attrs={'class': 'select select-bordered'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'input input-bordered'}),
            'city': forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Ex: Cotonou'}),
            'country': forms.TextInput(attrs={'class': 'input input-bordered', 'placeholder': 'Ex: Bénin'}),
            'bio': forms.Textarea(attrs={'class': 'textarea textarea-bordered h-32', 'placeholder': 'Parlez un peu de vous...'}),
            'relationship_goal': forms.Select(attrs={'class': 'select select-bordered'}),
            'is_diaspora': forms.CheckboxInput(attrs={'class': 'checkbox checkbox-primary'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir les champs User si le profil existe
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        """
        Sauvegarde le Profil ET met à jour l'Avatar de l'User.
        """
        profile = super().save(commit=False)

        # 1. Mise à jour Nom/Prénom
        profile.user.first_name = self.cleaned_data['first_name']
        profile.user.last_name = self.cleaned_data['last_name']

        # 2. Mise à jour de l'AVATAR (si un fichier est uploadé)
        if 'avatar' in self.cleaned_data and self.cleaned_data['avatar']:
            profile.user.avatar = self.cleaned_data['avatar']

        # 3. Sauvegarder l'User d'abord (pour que l'image soit enregistrée)
        profile.user.save()

        # 4. Sauvegarder le Profil
        if commit:
            profile.save()
        return profile


class ProfileImageForm(forms.Form):
    """Formulaire pour la photo de couverture (bannière)"""
    image = forms.ImageField(
        label="Image de couverture",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'file-input file-input-bordered w-full',
            'accept': 'image/*'
        })
    )

    def save(self, profile):
        """
        Sauvegarde SEULEMENT si un fichier est fourni.
        """
        image_file = self.cleaned_data.get('image')
        
        if image_file:  # On crée uniquement s'il y a une image
            # Supprimer l'ancienne couverture
            profile.images.filter(is_cover=True).delete()
            
            # Créer la nouvelle
            ProfileImage.objects.create(
                profile=profile,
                image=image_file,
                is_cover=True
            )