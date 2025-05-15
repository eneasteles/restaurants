from django import forms
from .models import Restaurant, MenuItem, Customer


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'slug', 'address', 'phone', 'email', 'logo', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'slug': 'Parte da URL que identifica seu restaurante (letras, números e hífens)'
        }



class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'is_available', 'preparation_time', 'ingredients']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'ingredients': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'preparation_time': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        restaurant_id = kwargs.pop('restaurant_id', None)
        super().__init__(*args, **kwargs)
        self.fields['price'].help_text = "Deixe em branco para usar o preço do item automaticamente"
        
        if restaurant_id:
            self.fields['category'].queryset = self.fields['category'].queryset.filter(restaurant_id=restaurant_id)



class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

# restaurants/forms.py (adicionar isso)



