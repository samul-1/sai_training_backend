from django.contrib import admin
from users.models import User

from training.models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    pass


@admin.register(ProgrammingExercise)
class ProgrammingExerciseAdmin(admin.ModelAdmin):
    pass


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass


@admin.register(TrainingTemplateRule)
class TrainingTemplateRuleAdmin(admin.ModelAdmin):
    pass


@admin.register(TrainingTemplate)
class TrainingTemplateAdmin(admin.ModelAdmin):
    pass


class TrainingSessionQuestionInline(admin.TabularInline):
    model = TrainingSession.questions.through


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    inlines = [TrainingSessionQuestionInline]
