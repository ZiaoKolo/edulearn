from django.shortcuts import render
from courses.models import Course

def home_view(request):
    # Récupérer quelques cours populaires (par exemple, ceux avec le plus d'étudiants)
    popular_courses = Course.objects.all().order_by('-students')[:3]
    
    context = {
        'popular_courses': popular_courses,
    }
    
    return render(request, 'home.html', context)