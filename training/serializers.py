from rest_framework import serializers

from .models import (
    Choice,
    Course,
    ExerciseSubmission,
    ExerciseTestCase,
    ProgrammingExercise,
    Question,
    Topic,
    TrainingSession,
    TrainingTemplate,
    TrainingTemplateRule,
)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["name", "description", "creator"]
        teachers_only_fields = ["allowed_teachers"]

    def __init__(self, *args, **kwargs):  # todo probably make a mixin for this behavior
        if self.context["request"].user.is_teacher:
            self.fields.extend(self.teachers_only_fields)

        super().__init__(*args, **kwargs)


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["name", "description", "items_type"]
        teachers_only_fields = ["help_text", "error_percentage_for_help_text"]

    def __init__(self, *args, **kwargs):
        if self.context["request"].user.is_teacher:
            self.fields.extend(self.teachers_only_fields)

        super().__init__(*args, **kwargs)


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["text"]
        teachers_only_fields = ["correct"]

    def __init__(self, *args, **kwargs):
        if self.context["request"].user.is_teacher:
            self.fields.extend(self.teachers_only_fields)

        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"].source = "rendered_text"


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["text"]
        teachers_only_fields = ["solution"]

    def __init__(self, *args, **kwargs):
        if self.context["request"].user.is_teacher:
            self.fields.extend(self.teachers_only_fields)

        super().__init__(*args, **kwargs)
        self.fields["choices"] = ChoiceSerializer(many=True, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"].source = "rendered_text"
            self.fields["solution"].source = "rendered_solution"
