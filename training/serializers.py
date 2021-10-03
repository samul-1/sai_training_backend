from rest_framework import serializers

from training.models import (
    QuestionTrainingSessionThroughModel,
    TestCaseOutcomeThroughModel,
)

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
    creator = serializers.CharField(source="creator.full_name", required=False)
    creator_id = serializers.IntegerField(source="creator.pk", required=False)

    class Meta:
        model = Course
        fields = ["id", "name", "description", "creator", "number_enrolled"]
        teachers_only_fields = ["allowed_teachers", "creator_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["enrolled"] = serializers.SerializerMethodField()
            self.fields["in_progress_session"] = serializers.SerializerMethodField()

    def get_enrolled(self, obj):
        return self.context["request"].user in obj.enrolled_students.all()

    def get_in_progress_session(self, obj):
        return TrainingSession.objects.filter(
            trainee=self.context["request"].user,
            course=obj,
            in_progress=True,
        ).exists()


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"] = serializers.CharField(source="rendered_text")


class PostSessionQuestionSerializer(ReadOnlyModelSerializer):
    text = serializers.CharField(source="question.rendered_text")
    solution = serializers.CharField(source="question.rendered_solution")
    id = serializers.IntegerField(source="question.id")

    class Meta:
        model = QuestionTrainingSessionThroughModel
        fields = ["id", "text", "solution", "selected_choice"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        kwargs.pop("source")
        self.fields["choices"] = PostSessionChoiceSerializer(
            source="question.choices", many=True, **kwargs
        )


class TrainingSessionOutcomeSerializer(ReadOnlyModelSerializer):
    help_texts = serializers.DictField(source="relevant_help_texts")

    class Meta:
        model = TrainingSession
        fields = [
            "id",
            "score",
            "questions",
            "begin_timestamp",
            "end_timestamp",
            "help_texts",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["questions"] = PostSessionQuestionSerializer(
            many=True, source="questiontrainingsessionthroughmodel_set", **kwargs
        )


class QuestionSerializer(TeachersOnlyFieldsModelSerializer):
    # send difficulty as string rather than number for easier manipulation in frontend
    difficulty = serializers.CharField()

    class Meta:
        model = Question
        fields = ["id", "text", "imported_from_exam", "topic"]
        read_only_fields = ["imported_from_exam"]
        teachers_only_fields = ["solution", "difficulty"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # parameter `many` gets passed from the view to handle possible bulk creation:
        # need to pop it to avoid passing it onto the ChoiceSerializer
        kwargs.pop("many", None)

        self.fields["choices"] = ChoiceSerializer(many=True, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"] = serializers.CharField(source="rendered_text")

    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        question = Question.objects.create(**validated_data)

        # create objects for each choice
        for choice in choices_data:
            Choice.objects.create(question=question, **choice)

        return question

    def update(self, instance, validated_data):
        # get data about choices
        choices_data = validated_data.pop("choices")

        # update question instance
        instance = super().update(instance, validated_data)

        choices = instance.choices.all()

        # update each choice
        for choice_data in choices_data:
            if choice_data.get("id") is not None:
                choice = Choice.objects.get(pk=choice_data["id"])
                save_id = choice_data.pop("id")
            else:
                choice = Choice.objects.create(
                    question=instance,
                    correct=True,  # dummy value for db constraint, will be overwritten by whatever is in `choice_data`
                )
                save_id = choice.pk

            serializer = ChoiceSerializer(
                choice, data=choice_data, context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=choice, validated_data=choice_data)

            # remove choice from the list of those still to process
            choices = choices.exclude(pk=save_id)

        # remove any choices for which data wasn't sent (i.e. user deleted them)
        for choice in choices:
            choice.delete()

        return instance


class TestCaseOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCaseOutcomeThroughModel
        fields = ["passed", "details"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["code"] = serializers.CharField(source="testcase.code")


class SubmissionSerializer(serializers.ModelSerializer):
    outcomes = TestCaseOutcomeSerializer(
        source="testcaseoutcomethroughmodel_set", many=True
    )

    class Meta:
        model = ExerciseSubmission
        fields = ["id", "code", "outcomes", "error"]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(user=self.context["request"].user)


class ExerciseTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseTestCase
        fields = ["code"]


class ProgrammingExerciseSerializer(TeachersOnlyFieldsModelSerializer):
    # send difficulty as string rather than number for easier manipulation in frontend
    difficulty = serializers.CharField()

    class Meta:
        model = ProgrammingExercise
        fields = ["id", "text", "imported_from_exam", "topic", "testcases"]
        read_only_fields = ["imported_from_exam"]
        teachers_only_fields = ["solution", "difficulty"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # parameter `many` gets passed from the view to handle possible bulk creation:
        # need to pop it to avoid passing it onto the ChoiceSerializer
        kwargs.pop("many", None)

        self.fields["testcases"] = ExerciseTestCaseSerializer(many=True, **kwargs)

        if not self.context["request"].user.is_teacher:
            self.fields["text"] = serializers.CharField(source="rendered_text")

            self.fields["submissions"] = SubmissionSerializer(many=True)


class TrainingSessionSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = TrainingSession
        fields = ["id", "questions", "begin_timestamp"]

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

    def update(self, instance, validated_data):
        rules_data = validated_data.pop("trainingtemplaterule_set")

        instance = super().update(instance, validated_data)

        instance.rules.clear()

        for rule_data in rules_data:
            topic_data = rule_data.pop("topic")
            print(topic_data)
            topic = Topic.objects.get(name=topic_data["name"], course=instance.course)
            rule = TrainingTemplateRule.objects.create(
                training_template=instance, topic=topic, **rule_data
            )
            instance.rules.add()

        return instance
