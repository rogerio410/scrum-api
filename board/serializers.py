from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Sprint, Task

from django.urls import reverse

from datetime import date

from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class SprintSerializer(serializers.ModelSerializer):

    links = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = ('id', 'name', 'description', 'end', 'links', )

    def get_links(self, obj):
        request = self.context['request']
        return {
            'self': reverse('sprint-detail',
                            kwargs={'pk': obj.pk}),
            'tasks': reverse('task-list') + '?sprint={}'.format(obj.pk),
        }

    def validate_end(self, value):
        new = self.instance is None
        updated = not new and self.initial_data['end'] != self.instance.end
        if (new or updated) and value < date.today():
            msg = _('End date cannot be in the past.')
            raise serializers.ValidationError(msg)
        return value


class TaskSerializer(serializers.ModelSerializer):

    status_display = serializers.SerializerMethodField()
    assigned = serializers.SlugRelatedField(slug_field=User.USERNAME_FIELD, required=False, read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'name', 'description', 'sprint', 'status', 'status_display', 'order',
            'assigned', 'started', 'due', 'completed', )

    def get_status_display(self, obj):
        return obj.get_status_display()

    def validate_sprint(self, value):
        orig_task = getattr(self, 'instance', None)
        orig_sprint = getattr(orig_task, 'sprint', None)
        sprint = value
        if (getattr(orig_sprint, 'id', None) != getattr(sprint, 'id', None) and
                    int(self.initial_data['status']) == Task.STATUS_DONE):
            raise serializers.ValidationError(_('Cannot change the sprint of a completed task.'))
        if getattr(sprint, 'end', date.today()) < date.today():
            raise serializers.ValidationError(_('Cannot assign tasks to past sprints'))
        return value

    def validate(self, data):
        sprint = data.get('sprint', None)
        status = data.get('status', None)
        started = data.get('started', None)
        completed = data.get('completed', None)
        if not sprint and status != Task.STATUS_TODO:
            raise serializers.ValidationError(_('Backlog tasks must have "Not Started" status.'))
        if started and status == Task.STATUS_TODO:
            raise serializers.ValidationError(_('"Not Started" tasks cannot have a start date.'))
        if completed and status != Task.STATUS_DONE:
            raise serializers.ValidationError(
                _('Completed date cannot be set for incomplete tasks.'))
        if status == Task.STATUS_DONE and not completed:
            raise serializers.ValidationError(_('Completed tasks must have a completed date'))
        return data


class UserSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ('id', User.USERNAME_FIELD, 'full_name', 'is_active', )