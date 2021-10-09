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


class NestedCreateUpdateSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # assumes the validated_data dict contains a field that is named with
        # the plural name of the child model
        children_data = validated_data.pop(self.child_model._meta.verbose_name_plural)

        instance = self.Meta.model.objects.create(**validated_data)

        # the kwarg used to reference the parent instance has the same name as the parent class
        parent_kwarg = {f"{self.Meta.model._meta.verbose_name}": instance}

        # create a related object for each child
        for child in children_data:
            self.child_model.objects.create(**parent_kwarg, **child)

        return instance

    def update(self, instance, validated_data):
        # assumes the validated_data dict contains a field that is named with
        # the plural name of the child model
        children_data = validated_data.pop(self.child_model._meta.verbose_name_plural)

        # update main instance
        instance = super().update(instance, validated_data)

        children = getattr(instance, self.child_model._meta.verbose_name_plural).all()

        # update or create each child
        for child_data in children_data:
            if child_data.get("id") is not None:  # an existing child is being updated
                child = self.child_model.objects.get(pk=child_data["id"])
                save_id = child_data.pop("id")
            else:  # a new child needs to be created
                # the kwarg used to reference the parent instance has the same name as the parent class
                parent_kwarg = {f"{self.Meta.model._meta.verbose_name}": instance}
                child = self.child_model.objects.create(**child_data, **parent_kwarg)
                save_id = child.pk

            serializer = self.child_serializer(
                child, data=child_data, context=self.context
            )
            serializer.is_valid(raise_exception=True)
            serializer.update(instance=child, validated_data=child_data)

            # remove child from the list of those still to process
            children = children.exclude(pk=save_id)

        # children that are still in the queryset at this point were
        # deleted in the frontend because no data was sent for them
        for child in children:
            child.delete()

        return instance


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
        fields = [
            "id",
            "name",
            "description",
            "creator",
            "number_enrolled",
            "uses_programming_exercises",
        ]
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
    is_open_ended = serializers.BooleanField(source="question.is_open_ended")
    id = serializers.IntegerField(source="question.id")

    class Meta:
        model = QuestionTrainingSessionThroughModel
        fields = [
            "id",
            "text",
            "solution",
            "selected_choice",
            "is_open_ended",
            "open_answer_text",
        ]

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


class QuestionSerializer(
    TeachersOnlyFieldsModelSerializer, NestedCreateUpdateSerializer
):
    # send difficulty as string rather than number for easier manipulation in frontend
    difficulty = serializers.CharField()

    child_model = Choice
    child_serializer = ChoiceSerializer

    class Meta:
        model = Question
        fields = ["id", "text", "imported_from_exam", "topic", "is_open_ended"]
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
        fields = ["id", "code", "outcomes", "error", "timestamp"]


class ExerciseTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseTestCase
        fields = ["code"]


class ProgrammingExerciseSerializer(
    TeachersOnlyFieldsModelSerializer, NestedCreateUpdateSerializer
):
    # send difficulty as string rather than number for easier manipulation in frontend
    difficulty = serializers.CharField()

    child_model = ExerciseTestCase
    child_serializer = ExerciseTestCaseSerializer

    class Meta:
        model = ProgrammingExercise
        fields = [
            "id",
            "text",
            "imported_from_exam",
            "topic",
            "testcases",
            "initial_code",
        ]
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

            self.fields["submissions"] = serializers.SerializerMethodField()

    def get_submissions(self, obj):
        qs = obj.submissions.filter(user=self.context["request"].user)
        serializer = SubmissionSerializer(instance=qs, many=True)
        return serializer.data


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
            topic = Topic.objects.get(name=topic_data["name"], course=instance.course)
            rule = TrainingTemplateRule.objects.create(
                training_template=instance, topic=topic, **rule_data
            )
            instance.rules.add()

        return instance
