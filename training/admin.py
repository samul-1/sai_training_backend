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


class EnrollmentInline(admin.TabularInline):
    model = Course.enrolled_students.through


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [EnrollmentInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass


@admin.register(TrainingTemplateRule)
class TrainingTemplateRuleAdmin(admin.ModelAdmin):
    pass


class TrainingTemplateRuleInline(admin.TabularInline):
    model = TrainingTemplate.rules.through
    readonly_fields = ("amount",)
    # fieldsets = (
    #     (
    #         None,
    #         {
    #             "fields": (("amount"),),
    #         },
    #     ),
    # )


@admin.register(TrainingTemplate)
class TrainingTemplateAdmin(admin.ModelAdmin):
    inlines = [TrainingTemplateRuleInline]


class TrainingSessionQuestionInline(admin.TabularInline):
    model = TrainingSession.questions.through


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    inlines = [TrainingSessionQuestionInline]
