from rest_framework import serializers

from training.models import QuestionTrainingSessionThroughModel

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


class ReadOnlyModelSerializer(serializers.ModelSerializer):
    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        for field in fields:
            fields[field].read_only = True
        return fields


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
    creator = serializers.CharField(source="creator.full_name")

    class Meta:
        model = Course
        fields = ["id", "name", "description", "creator", "number_enrolled"]
        teachers_only_fields = ["allowed_teachers"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["enrolled"] = serializers.SerializerMethodField()

    def get_enrolled(self, obj):
        return self.context["request"].user in obj.enrolled_students.all()


class TopicSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "description", "items_type"]
        teachers_only_fields = ["help_text", "error_percentage_for_help_text"]


class ChoiceSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]
        teachers_only_fields = ["correct"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"] = serializers.CharField(source="rendered_text")


class PostSessionChoiceSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "correct"]


class PostSessionQuestionSerializer(ReadOnlyModelSerializer):
    choices = PostSessionChoiceSerializer(source="question.choices", many=True)
    text = serializers.CharField(source="question.rendered_text")
    solution = serializers.CharField(source="question.rendered_solution")
    id = serializers.IntegerField(source="question.id")

    class Meta:
        model = QuestionTrainingSessionThroughModel
        fields = ["id", "text", "solution", "choices", "selected_choice"]


class TrainingSessionOutcomeSerializer(ReadOnlyModelSerializer):
    questions = PostSessionQuestionSerializer(
        many=True, source="questiontrainingsessionthroughmodel_set"
    )

    class Meta:
        model = TrainingSession
        fields = ["id", "score", "questions", "begin_timestamp", "end_timestamp"]


# class ListQuestionSerializer(serializers.ListSerializer):
#     def create(self, validated_data):
#         # questions = [Question(choices=set(choices), **data) for {"choices": choices, **data} in validated_data]
#         questions = []
#         for question_data in validated_data:
#             choices = question_data.pop("choices")
#             question = Question(**question_data)
#             question.choices.set(choices)
#             questions.append(question)
#         return Question.objects.bulk_create(questions, ignore_conflicts=True)


class QuestionSerializer(TeachersOnlyFieldsModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "imported_from_exam", "topic"]
        read_only_fields = ["imported_from_exam"]
        teachers_only_fields = ["solution", "difficulty"]
        # list_serializer_class = ListQuestionSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["choices"] = ChoiceSerializer(many=True, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"] = serializers.CharField(source="rendered_text")

    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        print("VALIDATED DATA")
        print(validated_data)
        question = Question.objects.create(**validated_data)

        # create objects for each choice
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)

        return question


class TrainingSessionSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = TrainingSession
        fields = ["questions", "begin_timestamp"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["questions"] = QuestionSerializer(many=True, **kwargs)


class TrainingTemplateRuleSerializer(serializers.ModelSerializer):
    difficulty_profile = serializers.CharField(source="difficulty_profile_code")
    topic = serializers.CharField(source="topic.name")
    amount = serializers.IntegerField()

    class Meta:
        model = TrainingTemplateRule
        fields = ["topic", "amount", "difficulty_profile"]


class TrainingTemplateSerializer(serializers.ModelSerializer):
    rules = TrainingTemplateRuleSerializer(source="trainingtemplaterule_set", many=True)

    class Meta:
        model = TrainingTemplate
        fields = ["id", "rules", "name", "description", "custom"]

    def create(self, validated_data):
        rules_data = validated_data.pop("trainingtemplaterule_set")

        template = TrainingTemplate.objects.create(**validated_data)

        # create objects for each rule
        for rule in rules_data:
            topic_data = rule.pop("topic")
            topic = Topic.objects.get(course=template.course, name=topic_data["name"])
            TrainingTemplateRule.objects.create(
                training_template=template, topic=topic, **rule
            )

        return template
