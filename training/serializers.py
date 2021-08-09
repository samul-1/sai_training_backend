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


class TeachersOnlyFieldsModelSerializer(serializers.ModelSerializer):
    # Used to only show certain fields of the serialized model to teachers. At
    # initialization, checks if the requesting user is a teacher: if it is, the
    # fields in `teachers_only_fields` are displayed on top of the regular ones
    def __init__(self, *args, **kwargs):
        self.Meta.fields.extend(self.Meta.teachers_only_fields)
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            for field in self.Meta.teachers_only_fields:
                self.fields.pop(field)


class CourseSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Course
        fields = ["name", "description", "creator"]
        teachers_only_fields = ["allowed_teachers"]


class TopicSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Topic
        fields = ["name", "description", "items_type"]
        teachers_only_fields = ["help_text", "error_percentage_for_help_text"]


class ChoiceSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Choice
        fields = ["text"]
        teachers_only_fields = ["correct"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            # self.fields["text"].source = "rendered_text"
            self.fields["text"] = serializers.CharField(source="rendered_text")


class QuestionSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Question
        fields = ["text", "imported_from_exam"]
        read_only_fields = ["imported_from_exam"]
        teachers_only_fields = ["solution", "difficulty"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["choices"] = ChoiceSerializer(many=True, **kwargs)

        if not self.context["request"].user.is_teacher:
            # self.fields["text"].source = "rendered_text"
            self.fields["text"] = serializers.CharField(source="rendered_text")

    def create(self, validated_data):
        choices_data = validated_data.pop("choices")

        question = Question.objects.create(**validated_data)

        # create objects for each choice
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)

        return question


class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = "__all__"


class TrainingTemplateRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingTemplateRule
        fields = ["topic", "difficulty_profile_code", "amount"]


class TrainingTemplateSerializer(serializers.ModelSerializer):
    rules = TrainingTemplateRuleSerializer(source="trainingtemplaterule_set", many=True)

    class Meta:
        model = TrainingTemplate
        fields = "__all__"

    def create(self, validated_data):
        rules_data = validated_data.pop("rules")

        template = TrainingTemplate.objects.create(**validated_data)

        # create objects for each rule
        for rule in rules_data:
            TrainingTemplateRule.objects.create(template=template, **rule)

        return template
