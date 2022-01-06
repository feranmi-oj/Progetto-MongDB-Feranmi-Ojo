from django import forms


class Order_Form(forms.Form):
	price = forms.FloatField(label='Price($)',widget=forms.TextInput(attrs={'class': 'white-text'}))
	quantity = forms.FloatField(label='Quantity(BTC)',widget=forms.TextInput(attrs={'class': 'white-text'}))
	limit = forms.FloatField(label='Limit($)',widget=forms.TextInput(attrs={'class': 'white-text'}))

	def clean(self):
			cleaned_data = super().clean()
			price = self.cleaned_data.get('price')
			quantity = self.cleaned_data.get('quantity')
			limit = self.cleaned_data.get('limit')
			if price < 0:
				raise forms.ValidationError('') #display messages.error instead
			if limit < 0:
				raise forms.ValidationError('') #display messages.error instead
			if quantity < 0:
				raise forms.ValidationError('') #display messages.error instead

			return cleaned_data