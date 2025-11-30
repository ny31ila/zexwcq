# service-backend/assessment/admin.py
from django.contrib import admin, messages
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from .models import TestPackage, Assessment, UserAssessmentAttempt, AssessmentTestRunner
from .tests.test_runner import discover_tests, run_tests

@admin.register(TestPackage)
class TestPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'min_age', 'max_age', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'min_age', 'max_age')
    search_fields = ('name', 'description')
    ordering = ['min_age', 'name']
    filter_horizontal = ('assessments',)

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'json_filename', 'is_active')
    list_filter = ('is_active', 'created_at', 'packages')
    search_fields = ('name', 'description', 'json_filename')
    ordering = ['name']

@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'assessment', 'is_completed', 'start_time', 'end_time')
    list_filter = ('is_completed', 'start_time', 'assessment__packages')
    search_fields = ('user__national_code', 'user__first_name', 'user__last_name', 'assessment__name')
    readonly_fields = ('start_time', 'created_at', 'updated_at')

@admin.register(AssessmentTestRunner)
class AssessmentTestRunnerAdmin(admin.ModelAdmin):

    # This is a proxy model, so we don't want to see a list of actual 'Assessment' objects.
    # We override the changelist_view to show our custom test runner interface.
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Discover all available tests
        available_tests = discover_tests()

        # The results will be passed via the messages framework after a redirect.
        # We don't need to fetch them here, the template will render them.

        extra_context['available_tests'] = available_tests
        extra_context['title'] = "Assessment Test Runner"

        return super().changelist_view(request, extra_context=extra_context)

    # Add custom URLs for running tests
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('run-all/', self.admin_site.admin_view(self.run_all_tests_view), name='assessment_assessmenttestrunner_run_all'),
            path('run-specific/', self.admin_site.admin_view(self.run_specific_test_view), name='assessment_assessmenttestrunner_run_specific'),
        ]
        return custom_urls + urls

    # View to handle running all tests
    def run_all_tests_view(self, request):
        if request.method == 'POST':
            results = run_tests()
            for result in results:
                if result['result'] == 'PASS':
                    messages.success(request, f"PASS: {result['test']}")
                else:
                    # Use preformatted tag to preserve traceback formatting
                    error_message = f"<pre>{result['error']}</pre>"
                    messages.error(request, f"FAIL: {result['test']}", extra_tags=error_message)

        # Redirect back to the changelist view to display results
        return HttpResponseRedirect(reverse('admin:assessment_assessmenttestrunner_changelist'))

    # View to handle running a specific test
    def run_specific_test_view(self, request):
        if request.method == 'POST':
            test_path = request.POST.get('test_path')
            if test_path:
                results = run_tests(test_path=test_path)
                for result in results:
                    if result['result'] == 'PASS':
                        messages.success(request, f"PASS: {result['test']}")
                    else:
                        error_message = f"<pre>{result['error']}</pre>"
                        messages.error(request, f"FAIL: {result['test']}", extra_tags=error_message)

        return HttpResponseRedirect(reverse('admin:assessment_assessmenttestrunner_changelist'))

    # --- Disable standard model admin actions ---
    # We don't want to add, change, or delete these proxy objects.

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Remove the "actions" dropdown from the changelist
    def get_actions(self, request):
        return None
