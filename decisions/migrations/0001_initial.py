# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-22 12:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('iri', models.CharField(help_text='IRI for this action', max_length=255)),
                ('title', models.CharField(help_text='Title of the action', max_length=255)),
                ('ordering', models.IntegerField(help_text='Ordering of this action within a meeting')),
                ('article_number', models.CharField(help_text='The article number given to this action after decision', max_length=255, null=True)),
                ('proposal_identifier', models.CharField(help_text='Identifier for this action used inside the meeting minutes. The format will vary between cities.', max_length=255)),
                ('resolution', models.CharField(blank=True, help_text='Resolution taken in this action (like tabled, decided...)', max_length=255, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('name', models.CharField(help_text="Area's name", max_length=255)),
                ('classification', models.CharField(blank=True, help_text='An area category, e.g. city', max_length=255)),
                ('identifier', models.CharField(blank=True, help_text='An issued identifier', max_length=255)),
                ('parent', models.ForeignKey(help_text='The area that contains this area', on_delete=django.db.models.deletion.CASCADE, to='decisions.Area')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('iri', models.CharField(help_text='IRI for this attachment', max_length=255)),
                ('file', models.CharField(help_text='FIXME: i should refer to a file', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('role', models.CharField(help_text='Role of the person in the event (chairman, secretary...', max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('iri', models.CharField(help_text='IRI for this case', max_length=255)),
                ('title', models.CharField(help_text='Descriptive compact title for this case', max_length=255)),
                ('summary', models.CharField(blank=True, help_text='Summary of this case. Typically a few sentences.', max_length=255)),
                ('category', models.CharField(blank=True, help_text='Category this case belongs to ("tehtäväluokka")', max_length=255)),
                ('creation_date', models.DateField(blank=True, help_text='Date this case was entered into system', null=True)),
                ('district', models.CharField(blank=True, help_text='Name of district (if any), that this issue is related to. ', max_length=255)),
                ('public', models.BooleanField(default=True, help_text='Is this case public?')),
                ('area', models.ForeignKey(blank=True, help_text='Geographic area this case is related to', null=True, on_delete=django.db.models.deletion.CASCADE, to='decisions.Area')),
                ('attachments', models.ManyToManyField(related_name='cases', to='decisions.Attachment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('iri', models.CharField(help_text='IRI for this content', max_length=255)),
                ('ordering', models.IntegerField(help_text='Ordering of this content within the larger context (like action)')),
                ('title', models.CharField(help_text='Title of this content', max_length=255)),
                ('type', models.CharField(help_text='Type of this content (options include: decision, proposal, proceedings...)', max_length=255)),
                ('hypertext', models.CharField(help_text='Content formatted with pseudo-HTML. Only a very restricted set of tags is allowed. These are: first and second level headings (P+H1+H2) and table (more may be added, but start from a minimal set)', max_length=255)),
                ('action', models.ForeignKey(help_text='Action that this content describes', on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='decisions.Action')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('name', models.CharField(help_text="The event's name", max_length=255)),
                ('description', models.TextField(help_text="The event's description")),
                ('classification', models.CharField(help_text="The event's category", max_length=255)),
                ('location', models.CharField(help_text="The event's location", max_length=255)),
                ('start_date', models.DateField(help_text='The time at which the event starts')),
                ('end_date', models.DateField(blank=True, help_text='The time at which the event ends', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('abstract', models.CharField(help_text='A one-line description of an organization', max_length=255)),
                ('description', models.TextField(help_text='An extended description of an organization')),
                ('classification', models.CharField(help_text='An organization category, e.g. committee', max_length=255)),
                ('name', models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=255)),
                ('founding_date', models.DateField(help_text='A date of founding')),
                ('image', models.URLField(blank=True, help_text='A URL of an image')),
                ('area', models.ForeignKey(blank=True, help_text='The geographic area to which this organization is related', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='organizations', to='decisions.Area')),
                ('parent', models.ForeignKey(help_text='The organization that contains this organization', on_delete=django.db.models.deletion.CASCADE, to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('name', models.CharField(help_text="A person's preferred full name", max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('label', models.CharField(help_text='A label describing the post', max_length=255)),
                ('start_date', models.DateField(help_text='The date on which the post was created')),
                ('end_date', models.DateField(blank=True, help_text='The date on which the post was eliminated', null=True)),
                ('role', models.CharField(help_text='The function that the holder of the post fulfills', max_length=255)),
                ('other_label', models.CharField(blank=True, help_text='An alternate label', max_length=255)),
                ('area', models.ForeignKey(blank=True, help_text='The geographic area to which this post is related', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='decisions.Area')),
                ('memberships', models.ManyToManyField(help_text='The memberships of the members of the organization and of the organization itself', related_name='posts', to='decisions.Membership')),
                ('organization', models.ForeignKey(help_text='The organization in which the post is held', on_delete=django.db.models.deletion.CASCADE, to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VoteCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('group', models.CharField(help_text='A group of voters', max_length=255)),
                ('option', models.CharField(help_text='An option in a vote event', max_length=255)),
                ('value', models.IntegerField(help_text='The number of votes for an option')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VoteEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='The time at which the resource was created')),
                ('modified_at', models.DateTimeField(auto_now=True, help_text='The time at which the resource was updated')),
                ('result', models.CharField(blank=True, help_text='The result of the vote event', max_length=255)),
                ('identifier', models.CharField(help_text='An issued identifier', max_length=255)),
                ('action', models.ForeignKey(help_text='The action to which this vote event applies', on_delete=django.db.models.deletion.CASCADE, related_name='vote_events', to='decisions.Action')),
                ('counts', models.ForeignKey(help_text='The number of votes for options', on_delete=django.db.models.deletion.CASCADE, related_name='vote_events', to='decisions.VoteCount')),
                ('legislative_session', models.ForeignKey(help_text='The meeting (event) where this vote took place', on_delete=django.db.models.deletion.CASCADE, to='decisions.Event')),
                ('organization', models.ForeignKey(help_text='The organization whose members are voting', on_delete=django.db.models.deletion.CASCADE, related_name='vote_events', to='decisions.Organization')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(help_text='The organization in which the person or organization is a member', on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='decisions.Organization'),
        ),
        migrations.AddField(
            model_name='membership',
            name='person',
            field=models.ForeignKey(help_text='Person who has membership in organization', on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='decisions.Person'),
        ),
        migrations.AddField(
            model_name='event',
            name='attendees',
            field=models.ManyToManyField(help_text='People attending this event', related_name='events', through='decisions.Attendance', to='decisions.Person'),
        ),
        migrations.AddField(
            model_name='event',
            name='organization',
            field=models.ForeignKey(help_text='The organization organizing the event', on_delete=django.db.models.deletion.CASCADE, related_name='events', to='decisions.Organization'),
        ),
        migrations.AddField(
            model_name='event',
            name='parent',
            field=models.ForeignKey(blank=True, help_text='The event that this event is a part of', null=True, on_delete=django.db.models.deletion.CASCADE, to='decisions.Event'),
        ),
        migrations.AddField(
            model_name='case',
            name='originator',
            field=models.ForeignKey(blank=True, help_text='Person or organization the proposed this case to the city', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cases', to='decisions.Person'),
        ),
        migrations.AddField(
            model_name='case',
            name='related_cases',
            field=models.ManyToManyField(help_text='Other cases that are related to this case', related_name='_case_related_cases_+', to='decisions.Case'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='attendee',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='decisions.Person'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='decisions.Event'),
        ),
        migrations.AddField(
            model_name='action',
            name='case',
            field=models.ForeignKey(help_text='Case this action is related to', on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='decisions.Case'),
        ),
        migrations.AddField(
            model_name='action',
            name='delegation',
            field=models.ForeignKey(blank=True, help_text='If this decision was delegated, this field will be filled and refers to the post that made the decision', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='decisions.Post'),
        ),
        migrations.AddField(
            model_name='action',
            name='event',
            field=models.ForeignKey(help_text='Event (if any) where this action took place', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='decisions.Event'),
        ),
        migrations.AddField(
            model_name='action',
            name='responsible_party',
            field=models.ForeignKey(help_text='The city organization responsible for this decision. If decision is delegated, this is the organization that delegated the authority.', on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='decisions.Organization'),
        ),
    ]