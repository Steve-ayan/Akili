from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from .models import Course, Module, CachedLesson
from .forms import CourseCreationForm 

# IMPORTANT FIX: Import the AI generation utility you created
from core.utils.ai_module_generator import trigger_module_generation
# If you decide to implement credit check later, uncomment this:
# from core.utils import check_tutor_credits 


class CourseDashboardView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Displays a list of all courses personalized for the logged-in user.
    """
    def get(self, request):
        # Retrieve all courses belonging to the current user
        user_courses = Course.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'courses': user_courses,
            'title': 'My Akili Courses',
        }
        
        return render(request, 'courses/dashboard.html', context)


class CourseCreationView(LoginRequiredMixin, View):
    """
    Developer 1 Task: Handles the form submission to create a new personalized course.
    """
    def get(self, request):
        # Display the form to select exam type and subject
        form = CourseCreationForm()
        context = {
            'form': form,
            'title': 'Create New Course',
        }
        return render(request, 'courses/course_creation.html', context)
        
    def post(self, request):
        form = CourseCreationForm(request.POST)
        
        if form.is_valid():
            exam_type = form.cleaned_data['exam_type']
            subject = form.cleaned_data['subject']
            
            # 1. Check if the user already has this exact course
            if Course.objects.filter(user=request.user, exam_type=exam_type, subject=subject).exists():
                return redirect(reverse('courses:dashboard')) 
            
            # --- Credit Check (Kept commented until implemented) ---
            # if not check_tutor_credits(request.user, amount=5): 
            #     return render(request, 'courses/course_creation.html', {'form': form, 'error': 'Insufficient credits.'})
            
            # 2. Create the Course instance
            new_course = Course.objects.create(
                user=request.user,
                exam_type=exam_type,
                subject=subject,
            )
            
            # 3. Trigger AI Module Generation (Uncommented and made functional)
            print(f"--- DEBUG: Starting AI generation for {exam_type} {subject}")
            success = trigger_module_generation(new_course)
            
            if not success:
                # Handle AI failure (Tier 4 Circuit Breaker)
                print(f"--- ERROR: AI generation FAILED for {new_course.id}. Deleting course.")
                new_course.delete() # Prevent a broken course from being saved
                return render(request, 'courses/course_creation.html', {
                    'form': form, 
                    'error': 'AI service failed to generate modules. Please try again.'
                })
            
            return redirect(reverse('courses:dashboard')) # Go back to dashboard after successful creation
            
        # --- DEBUG LINE FOR FORM ERRORS ---
        else:
            print("--- DEBUG: Form is NOT valid. Errors:", form.errors)
        # --- END DEBUG LINE ---
            
        context = {
            'form': form,
            'title': 'Create New Course',
            'error': 'Please correct the errors below.' # General error for invalid forms
        }
        return render(request, 'courses/course_creation.html', context)