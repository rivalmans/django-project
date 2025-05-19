from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Category, Transaction, Budget

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class TransactionForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'category', 'amount', 'description', 'date']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = Category.objects.none()

        transaction_type = None

        # 1. Якщо дані передані (POST або GET), беремо з них тип
        if self.data.get('transaction_type'):
            transaction_type = self.data.get('transaction_type')

        # 2. Якщо є instance (редагування існуючої транзакції)
        elif self.instance.pk:
            transaction_type = self.instance.transaction_type

        # 3. Якщо не вказано — використовуємо тип 'expense' за замовчуванням
        else:
            transaction_type = 'expense'

        if self.user and transaction_type in ['income', 'expense']:
            self.fields['category'].queryset = Category.objects.filter(
                user=self.user,
                transaction_type=transaction_type
            )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'transaction_type']


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'limit']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()


class DateRangeForm(forms.Form):
    start_date = forms.DateField(label="Від", widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label="До", widget=forms.DateInput(attrs={'type': 'date'}))

