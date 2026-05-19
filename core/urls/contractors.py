"""
URLs para contratistas.
"""

from django.urls import path
from core.views.contractors import ContractorsView, ContractorViewSet, ContractorEditModalView

app_name = "contractors"

urlpatterns = [
    path("contractors/", ContractorsView.as_view(), name="contractors_list"),
    path('api/v1/contractors/', ContractorViewSet.as_view(), name='contractors_api'),
    path('api/v1/contractors/<int:contractor_id>/', ContractorViewSet.as_view(), name='contractor_detail'),
    path('api/v1/contractors/<int:contractor_id>/edit-modal/', ContractorEditModalView.as_view(), name='contractor_edit_modal'),
    path('api/v1/contractors/create-modal/', ContractorEditModalView.as_view(), name='contractor_create_modal'),
]

