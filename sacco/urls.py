from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home_view, name='home-url'),
    path('users/', views.users_view, name='users-url'),
    path('manage-user/<int:id>/', views.manage_user, name='manage-user-url'),
    path('delete-user/<int:id>/', views.delete_user, name='delete-user-url'),
    path('manage-user/', views.manage_user, name='manage-user-url'),
    path('loan-plans/', views.loan_plans_list, name='loan-plans-url'),
    path('loan-plans/add/', views.loan_plan_add, name='loan-plan-add-url'),
    path('register/', views.register_view, name='register-url'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login-url'),
    path('logout/', LogoutView.as_view(next_page='login-url'), name='logout-url'),
    path('members/', views.members_list, name='members-list'),
    path('members/add/', views.member_add, name='member-add'),
    path('members/<int:id>/edit/', views.member_edit, name='member-edit'),
    path('members/<int:id>/delete/', views.member_delete, name='member-delete'),
    path('dashboard/', views.home_view, name='dashboard'),
    path('members/<int:id>/', views.member_detail, name='member-detail'),
    path('members/<int:id>/profile/', views.member_detail, name='member_detail'),
    path('members/<int:id>/toggle-status/', views.member_toggle_status, name='member_toggle_status'),
    path('members/search/', views.member_search_by_ref_number, name='member-search-by-ref'),

    # Savings
    path('savings/', views.savings_list, name='savings'),
    path('savings/add/', views.saving_add, name='saving-add'),
    path('savings/<int:id>/edit/', views.saving_edit, name='saving-edit'),
    path('savings/<int:id>/delete/', views.saving_delete, name='saving-delete'),
    path('savings/<int:id>/edit-type/', views.saving_edit_type, name='saving-edit-type'),
    # Loans
    path('loans/', views.loans_list, name='loans'),
    path('loans/add/', views.loan_add, name='loan-add'),
    path('loans/<int:loan_id>/edit/', views.loan_edit, name='loan-edit'),
    path('loans/<int:loan_id>/delete/', views.loan_delete, name='loan-delete'),
    path('loans/<int:loan_id>/', views.loan_detail, name='loan-detail'),
    path('loans/<int:loan_id>/schedule/', views.loan_schedule_view, name='loan-schedule-view'),
    path('loans/<int:loan_id>/schedule/pdf/', views.loan_schedule_view_pdf, name='loan-schedule-view-pdf'),
    path('loans/<int:loan_id>/download-repayments/', views.download_repayments_csv, name='download_repayments_csv'),

    # Loan Repayment
    path('loans/<int:loan_id>/repay/', views.loan_repayment, name='loan-repayment'),
    path('loans/<int:loan_id>/repayments/', views.loan_repayments_list, name='loan-repayments-list'),
    path('loans/<int:loan_id>/repayments/pdf/', views.loan_repayments_pdf, name='loan-repayments-pdf'),
    path('repayments/', views.repayments_page, name='repayments-page'),

    # Borrowers
    path('borrowers/', views.borrowers_list, name='borrowers-url'),
    path('borrowers/add/', views.borrower_add, name='borrower-add-url'),
    path('sources-of-income/add/', views.add_source_of_income, name='add-source-of-income'),
    path('sources-of-income/update/', views.update_source_of_income, name='update-source-of-income'),
    path('sources-of-income/delete/', views.delete_source_of_income, name='delete-source-of-income'),
    # Loan Product Types
    path('loan-product-types/', views.loan_product_type_list, name='loan-product-type-list'),
    path('loan-product-types/<int:id>/edit/', views.loan_product_type_edit, name='loan-product-type-edit'),
    path('loan-product-types/<int:id>/delete/', views.loan_product_type_delete, name='loan-product-type-delete'),

    # Loan Approvals
    path('loan-approvals/', views.loan_approvals, name='loan-approvals'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path("statement/<int:member_id>",views.generate_statement,name='statement-url'),
    path("statement/<int:member_id>/pdf", views.statement_pdf, name="statement-pdf"),
    path("general-statement/<int:member_id>", views.general_statement, name="general-statement"),
    path("general-statement/<int:member_id>/pdf", views.general_statement_pdf, name="general-statement-pdf"),
    path('loan-schedule/', views.loan_schedule, name='loan-schedule'),
    path('loan-schedule-pdf/', views.loan_schedule_pdf, name='loan-schedule-pdf'),
    path('upload-sql/', views.upload_sql_view, name='upload-sql'),
    path('members/<int:member_id>/next-of-kin/', views.next_of_kin_manage, name='next-of-kin-manage'),
    path('settings/', views.settings_page, name='settings-page'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)