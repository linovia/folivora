# -*- coding: utf-8 -*-


import json

from django.core.urlresolvers import reverse_lazy, reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from django.contrib import messages

from braces.views import LoginRequiredMixin, UserFormKwargsMixin

from .forms import (AddProjectForm, UpdateUserProfileForm,
    ProjectDependencyForm, ProjectMemberForm, CreateProjectMemberForm)
from .models import Project, UserProfile, ProjectDependency, ProjectMember
from .utils.views import SortListMixin


folivora_index = TemplateView.as_view(template_name='folivora/index.html')


class ListProjectView(LoginRequiredMixin, SortListMixin, ListView):
    model = Project
    context_object_name = 'projects'
    sort_fields = ['name']
    default_order = ('name',)

    def get_queryset(self):
#        return Project.objects.filter(members=self.request.user)
        return super(ListProjectView, self).get_queryset()


project_list = ListProjectView.as_view()


class AddProjectView(LoginRequiredMixin, UserFormKwargsMixin, CreateView):
    model = Project
    form_class = AddProjectForm
    template_name_suffix = '_add'


project_add = AddProjectView.as_view()


class UpdateProjectView(LoginRequiredMixin, TemplateView):
    model = Project
    template_name = 'folivora/project_update.html'

    dep_qs = ProjectDependency.objects.select_related('package').order_by('package__name')
    dep_form_class = inlineformset_factory(Project, ProjectDependency, extra=0,
        form=ProjectDependencyForm)

    member_qs = ProjectMember.objects.select_related('user').order_by('user__username')
    member_form_class = inlineformset_factory(Project, ProjectMember, extra=0,
        form=ProjectMemberForm)

    def get_context_data(self, **kwargs):
        context = super(UpdateProjectView, self).get_context_data(**kwargs)
        data = self.request.POST if self.request.method == 'POST' else None
        object = Project.objects.get(slug=self.kwargs['slug'])
        dep_form = self.dep_form_class(data, queryset=self.dep_qs,
                                       instance=object)
        member_form = self.member_form_class(data, instance=object,
                                             queryset=self.member_qs)
        add_member_form = CreateProjectMemberForm()
        context.update({
            'dep_form': dep_form,
            'member_form': member_form,
            'add_member_form': add_member_form,
            'project': object,
        })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        forms = [ctx['dep_form'], ctx['member_form']]
        if all(map(lambda f: f.is_valid, forms)):
            for form in forms:
                form.save()
            object = Project.objects.get(slug=kwargs['slug'])
            messages.success(request, _(u'Updated Project “{name}” '
                'successfully.').format(name=object.name))
            return HttpResponseRedirect(reverse('folivora_project_update',
                                                kwargs={'slug': object.slug}))
        return self.render_to_response(ctx)


project_update = UpdateProjectView.as_view()


class DeleteProjectView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('folivora_project_list')

    def delete(self, *args, **kwargs):
        object = self.get_object()
        if object:
            messages.success(self.request, _(u'Deleted project “{name}” '
                'successfully.').format(name=object.name))
        return super(DeleteView, self).delete(*args, **kwargs)


project_delete = DeleteProjectView.as_view()


class DetailProjectView(LoginRequiredMixin, DetailView):
    model = Project


project_detail = DetailProjectView.as_view()


class CreateProjectMemberView(LoginRequiredMixin, TemplateView):
    model = ProjectMember
    form_class = CreateProjectMemberForm

    def post(self, request, *args, **kwargs):
        form = CreateProjectMemberForm(request.POST)
        if form.is_valid():
            project_member = form.save(commit=False)
            project_member.project = Project.objects.get(slug=self.kwargs['slug'])
            project_member.state = ProjectMember.MEMBER
            project_member.save()
            member_form = ProjectMemberForm(instance=project_member)
            new_row = render_to_string('folivora/project_edit_member_row.html', {
                'f': member_form})
            context = {'new_row': new_row}
        else:
            context = {'error': json.dumps(form.errors)}
        return HttpResponse(json.dumps(context))


project_add_member = CreateProjectMemberView.as_view()


class UpdateUserProfileView(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserProfileForm
    def get_object(self, queryset=None):
        return self.request.user.get_profile()


profile_edit = UpdateUserProfileView.as_view()
