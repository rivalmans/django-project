from rest_framework import viewsets, permissions
from .models import Category, Transaction, Budget
from .serializers import CategorySerializer, TransactionSerializer, BudgetSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Q
from .forms import DateRangeForm, RegisterForm, TransactionForm, CategoryForm, BudgetForm
from django.contrib import messages
from django.http import JsonResponse

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class BudgetViewSet(viewsets.ModelViewSet):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


def index(request):
    return render(request, 'index.html')


@login_required
def dashboard(request):
    user = request.user
    form = DateRangeForm(request.GET or None)

    # Базовий фільтр
    transactions = Transaction.objects.filter(user=user).order_by('-date')

    # Якщо вказано діапазон дат — фільтруємо
    if form.is_valid():
        start = form.cleaned_data['start_date']
        end = form.cleaned_data['end_date']
        transactions = transactions.filter(date__range=(start, end))

    # Загальний дохід і витрати
    income = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
    expenses = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0

    # Витрати по категоріях
    categories = Category.objects.filter(user=user)
    category_data = []
    for category in categories:
        spent = transactions.filter(category=category, transaction_type='expense') \
            .aggregate(total=Sum('amount'))['total'] or 0

        budget = Budget.objects.filter(user=user, category=category).first()
        limit = budget.limit if budget else None
        percent_used = (spent / limit * 100) if limit and limit > 0 else None

        category_data.append({
            'name': category.name,
            'spent': float(spent),
            'limit': float(limit) if limit else None,
            'percent_used': round(percent_used, 2) if percent_used is not None else None,
            'over_budget': percent_used is not None and percent_used > 100
        })

    budgets = Budget.objects.filter(user=user)

    return render(request, 'dashboard.html', {
        'form': form,
        'income': income,
        'expenses': expenses,
        'transactions': transactions[:10],
        'category_data': category_data,
        'budgets': budgets,
    })


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Акаунт створено! Увійдіть, щоб продовжити.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@login_required
def add_transaction(request):
    # Підрахунок доходів та витрат користувача
    income = (
        Transaction.objects.filter(user=request.user, transaction_type='income')
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    expenses = (
        Transaction.objects.filter(user=request.user, transaction_type='expense')
        .aggregate(total=Sum('amount'))['total'] or 0
    )
    
    # Можна додати і category_data для графіка, якщо потрібно
    # Припустимо category_data - це список словників з потрібними полями
    # category_data = ...

    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Транзакцію додано успішно.')
            return redirect('dashboard')
    else:
        form = TransactionForm(user=request.user)

    context = {
        'form': form,
        'income': income,
        'expenses': expenses,
        # 'category_data': category_data,  # Якщо потрібно графік додати
    }
    return render(request, 'add_transaction.html', context)


@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Категорію додано успішно.')
            return redirect('dashboard')  # або на сторінку категорій
    else:
        form = CategoryForm()
    return render(request, 'add_category.html', {'form': form})


@login_required
def load_categories(request):
    transaction_type = request.GET.get('transaction_type')
    categories = Category.objects.filter(user=request.user, transaction_type=transaction_type).values('id', 'name')
    return JsonResponse({'categories': list(categories)})


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user)
    return render(request, 'budget_list.html', {'budgets': budgets})

@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST, user=request.user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            budget.save()
            return redirect('budget_list')
    else:
        form = BudgetForm(user=request.user)
    return render(request, 'budget_form.html', {'form': form})

@login_required
def budget_edit(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget, user=request.user)
    return render(request, 'budget_form.html', {'form': form})


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    return render(request, 'transactions/list.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Транзакцію додано успішно.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(user=request.user)
    return render(request, 'transactions/form.html', {'form': form, 'is_edit': False})

@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Транзакцію оновлено.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(request, 'transactions/form.html', {'form': form, 'is_edit': True})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Транзакцію видалено.')
        return redirect('transaction_list')
    return render(request, 'transactions/confirm_delete.html', {'transaction': transaction})

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'transactions/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'transactions/category_form.html', {'form': form, 'is_edit': False})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'transactions/category_form.html', {'form': form, 'is_edit': True})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'transactions/category_confirm_delete.html', {'category': category})

@login_required
def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'transactions/category_form.html', {'form': form, 'is_edit': True})

@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        return redirect('budget_list')
    return render(request, 'budget_confirm_delete.html', {'budget': budget})

@login_required
def load_categories(request):
    transaction_type = request.GET.get('transaction_type')
    categories = Category.objects.filter(user=request.user, transaction_type=transaction_type).values('id', 'name')
    return JsonResponse({'categories': list(categories)})


def index(request):
    return redirect('dashboard')

