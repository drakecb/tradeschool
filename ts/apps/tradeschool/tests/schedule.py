from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.conf import settings
from datetime import *
import shutil, os, os.path
from tradeschool.models import *



class ScheduleTestCase(TestCase):
    """ Tests the process of submitting a schedule using the frontend form.
    """
    fixtures = ['test_data.json', 'test_timerange.json']
    
    def setUp(self):
        """ Create a Site and branch for testing.
        """
        # test in english so we count html strings correctly
        settings.LANGUAGE_CODE = 'en'
        
        self.site   = Site.objects.all()[0]
        
        # change the language to english for language-based assertations
        self.branch = Branch.objects.all()[0]
        self.branch.language = 'en'
        self.branch.save()
        
        self.url = reverse('schedule-add', kwargs={'branch_slug' : self.branch.slug })
        
        self.time = Time.objects.filter(venue__isnull=True)[0]
        
        self.new_teacher_data = {
                'teacher-fullname'  : 'new test teahcer', 
                'teacher-bio'       : 'biobiobio', 
                'teacher-website'   : 'http://website.com', 
                'teacher-email'     : 'email@email.com', 
                'teacher-phone'     : '123-123-1234',
            }
        self.new_course_data = {
                'course-title'        : 'new test course', 
                'course-description'  : 'this is the description', 
                'course-max_students' : '20', 
            }
        self.time_data = {
                'time-time'             : self.time.pk
            } 
        self.barter_items_data = {
                'item-0-title'          : 'test item 01',
                'item-1-title'          : 'test item 02',
                'item-2-title'          : 'test item 03',
                'item-3-title'          : 'test item 04',
                'item-4-title'          : 'test item 05',
                'item-TOTAL_FORMS'      : 5,
                'item-INITIAL_FORMS'    : 0,
                'item-MAX_NUM_FORMS'    : 1000,                
            }
        self.empty_data = {
                'item-TOTAL_FORMS'      : 0,
                'item-INITIAL_FORMS'    : 0,
                'item-MAX_NUM_FORMS'    : 1000,
            }
        
        # merge the items of course, teacher, and barter item data
        self.valid_data = dict(self.new_course_data.items() + self.new_teacher_data.items() + self.barter_items_data.items() + self.time_data.items())
        

    def compare_schedule_to_data(self, schedule_obj):
        """ Asserts that the objects that were created after a successful schedule submission
            match the data that was used in the forms.
        """
        self.assertEqual(schedule_obj.course.title, self.valid_data['course-title'])
        self.assertEqual(schedule_obj.course.description, self.valid_data['course-description']) 
        self.assertEqual(schedule_obj.course.max_students, int(self.valid_data['course-max_students']))
        self.assertEqual(schedule_obj.start_time, self.time.start_time)
        self.assertEqual(schedule_obj.end_time, self.time.end_time)
        self.assertEqual(schedule_obj.venue, self.time.venue)        
        self.assertEqual(schedule_obj.course.teacher.fullname, self.valid_data['teacher-fullname'])
        self.assertEqual(schedule_obj.course.teacher.bio, self.valid_data['teacher-bio'])
        self.assertEqual(schedule_obj.course.teacher.email, self.valid_data['teacher-email'])
        self.assertEqual(schedule_obj.course.teacher.phone, self.valid_data['teacher-phone'])
        for item in schedule_obj.items.all():
            self.assertTrue(item.title in self.valid_data.values())            


    def test_view_loading(self):
        """ Tests that the schedule-add view loads properly.
            If there's a branch-specific template file, make sure it's loaded as well.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(self.branch.slug + '/schedule_add.html')


    def test_empty_submission(self):
        """ Tests that submitting an empty form results in the expected error messages.
        """        
        response = self.client.post(self.url, data=self.empty_data)

        # an empty form should return 8 errors for the required fields
        self.assertContains(response, 'Please', count=8)
        
        # the same template should be rendered
        self.assertTemplateUsed(self.branch.slug + '/schedule_submit.html')


    def is_successful_submission(self, data):
        """ Tests that the submission of a schedule with valid data works.
        """
        # post the data to the schedule submission form
        response = self.client.post(self.url, data=data, follow=True)
        
        self.assertRedirects(response, response.redirect_chain[0][0], response.redirect_chain[0][1])
        self.assertTemplateUsed(self.branch.slug + '/schedule_submitted.html')
        
        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])
        
        return response
                

    def test_schedule_submission_new_teacher_new_course(self):
        """ Tests the submission of a schedule of a new class by a new teacher.
        """
        # test that the form submission worked
        response = self.is_successful_submission(self.valid_data)

        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])
        
        
    def test_schedule_submission_existing_teacher_new_course(self):
        """ Tests the submission of a schedule of a new class by an existing teacher.
        """
        # get a Person who teaches in the branch
        existing_teacher = Teacher.objects.filter(branch=self.branch)[0]

        # use the existing teacher's email for the form submission
        # when the teacher-email matches an existing objects,
        # the schedule should be saved to the existing teacher object
        self.valid_data['teacher-email'] = existing_teacher.email
        
        # test that the form submission worked
        response = self.is_successful_submission(self.valid_data)

        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])


    def test_schedule_submission_existing_teacher_existing_course(self):
        """ Tests the submission of a schedule of an existing class by an existing teacher.
        """
        # get a Person who teaches in the branch
        existing_teacher = Teacher.objects.filter(branch=self.branch)[0]

        # use the existing teacher's email for the form submission
        # when the teacher-email matches an existing Person object,
        # the schedule should be saved to the existing Person object
        self.valid_data['teacher-email'] = existing_teacher.email

        # get an existing course in the branch
        existing_course = Course.objects.filter(branch=self.branch)[0]

        # use the existing course's title for the form submission
        # when the course-title matches an existing Course object,
        # the schedule should be saved to the existing Course object
        self.valid_data['course-title'] = existing_course.title
        
        # test that the form submission worked
        response = self.is_successful_submission(self.valid_data)

        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])


    def test_venue_is_saved(self):
        """ Tests a successful submission with a Time object that has 
            a Venue foreignkey.
        """
        # save a time-venue relationship
        self.time.venue = Venue.objects.filter(branch=self.branch)[0]
        self.time.save()
        
        # test that the form submission worked
        response = self.is_successful_submission(self.valid_data)

        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])
        

    def test_time_deleted_after_successful_submission(self):
        """ Tests that the selected Time object gets deleted 
            after a schedule has been submitted successfully.
        """
        # get Time object
        time = Time.objects.get(pk=self.time_data['time-time'])
                
        # post the data to the schedule submission form
        response = self.client.post(self.url, data=self.valid_data, follow=True)

        # check that the time object got deleted 
        self.assertFalse(Time.objects.filter(pk=time.pk).exists())

    
    def test_schedule_emails_are_generated(self):
        """ Tests that a ScheduleEmailContainer is created after a successful schedule submission,
            and that 7 emails are copied to it from the BranchEmailContainer.
        """
        # submit a schedule
        response = self.is_successful_submission(self.valid_data)
        
        schedule = response.context['schedule']        
        
        # check that one ScheduleEmailContainer was created for the schedule
        self.assertEqual(ScheduleEmailContainer.objects.filter(schedule=schedule).count(), 1)

        # check that the ScheduleEmailContainer has all 7 Email objects
        self.assertEqual(schedule.emails.emails.__len__(), 7)
        
        # store this object in a variable for convenience 
        bec = BranchEmailContainer.objects.filter(branch__in=schedule.course.branch.all())[0]
                
        # iterate over the emails in the schedule's ScheduleEmailContainer
        for email_name, schedule_email_obj in schedule.emails.emails.items():
            # find the same email type in the BranchEmailContainer, 
            # where the schedule emails were copied from
            default_email = getattr(bec, email_name)

            # verify that the email was copied correctly
            self.assertEqual(schedule_email_obj.subject, default_email.subject)
            self.assertEqual(schedule_email_obj.content, default_email.content)        
        
    
    def test_teacher_confirmation_email(self):
        """ Tests that the TeacherConfirmation is sent after
            a successful submission.
        """
        # submit a schedule
        response = self.is_successful_submission(self.valid_data)        
        
        schedule = response.context['schedule']
        
        # test that one message was sent.
        self.assertEqual(len(mail.outbox), 1)        

        # verify the email status was updated
        email = schedule.emails.teacher_confirmation        
        self.assertEqual(email.email_status, 'sent')
        
        # verify that the subject of the message is correct.
        self.assertEqual(mail.outbox[0].subject, email.subject)
        


    def test_schedule_status(self):
        """ Tests that the only approved schedules appear on the schedule-list view.
        """
        # submit a schedule
        response = self.is_successful_submission(self.valid_data)        
        
        schedule = response.context['schedule']
        url = reverse('schedule-list', kwargs={'branch_slug' : self.branch.slug, })
        
        # go to schedule-list view
        response = self.client.get(url)
        
        # verify that the schedule is not on the page
        self.assertNotContains(response, schedule.course.title)
        
        # approve the schedule
        schedule.course_status = 3 
        schedule.save()
        
        # reload the page
        response = self.client.get(url)
        
        # verify that the schedule appears on the page
        self.assertContains(response, schedule.course.title)
        
    
    def test_teacher_approval_email(self):
        """ Tests that the TeacherClassApproval is sent after a schedule is approved.
        """
        # submit a schedule
        response = self.is_successful_submission(self.valid_data)        
        
        schedule = response.context['schedule']
        url = reverse('schedule-list', kwargs={'branch_slug' : self.branch.slug, })        
        
        # empty the test outbox
        mail.outbox = []
                
        # approve the schedule
        schedule.course_status = 3 
        schedule.save()
        
        # test that one message was sent.
        self.assertEqual(len(mail.outbox), 1)        

        # verify the email status was updated
        email = schedule.emails.teacher_class_approval
        self.assertEqual(email.email_status, 'sent')            
        
        # verify that the subject of the message is correct.
        self.assertEqual(mail.outbox[0].subject, email.subject)
                
        
    def test_edit_schedule_template(self):
        """ Test that the schedule-edit view doesn't load unless 
            a schedule_slug for an existing Schedule object is provided.
        """
        # try to load the schedule-edit view without a schedule slug
        response = self.client.get(reverse('schedule-edit', kwargs={'branch_slug':self.branch.slug, 'schedule_slug':None}))
        
        # this should lead to a 404 page
        self.assertEqual(response.status_code, 404)
        
        # post a valid schedule data to save a new schedule
        response = self.client.post(self.url, data=self.valid_data, follow=True)
        
        # try loading the schedule-edit view for the saved schedule
        response = self.client.get(reverse('schedule-edit', kwargs={'branch_slug':self.branch.slug, 'schedule_slug':response.context['schedule'].slug }))
        
        # check that the correct template was loaded sucessfully
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(self.branch.slug + '/schedule_edit.html')
        
        
    def test_editing_schedule_with_empty_data(self):
        """ Test that editting an existing Schedule and submitting an empty
            form results in the expected number of errors.
        """
        # post a valid schedule data to save a new schedule
        response = self.client.post(self.url, data=self.valid_data, follow=True)
        
        schedule = response.context['schedule']
        schedule_edit_url = reverse('schedule-edit', kwargs={'branch_slug':self.branch.slug, 'schedule_slug':schedule.slug })
        
        # post empty data to the form
        response = self.client.post(schedule_edit_url, data=self.empty_data)
        
        # an empty form should return 7 errors for the required fields
        # there's one less error when editing a schedule sine the time 
        # is already saved and can't be edited in the form
        self.assertContains(response, 'Please', count=7)


    def test_editing_schedule_with_valid_data(self):
        """ Test that editting an existing Schedule and submitting edited
            fields results in the new data being saved correctly.
            This includes any new BarterItem objects that may have been added
            to the form.
        """        
        # post a valid schedule data to save a new schedule
        response = self.client.post(self.url, data=self.valid_data, follow=True)

        schedule = response.context['schedule']
        schedule_edit_url = reverse('schedule-edit', kwargs={'branch_slug':self.branch.slug, 'schedule_slug':schedule.slug })
    
        # make some changes to the data
        for key, value in self.new_teacher_data.items():
            self.valid_data[key] = "1%s" % value
        for key, value in self.new_course_data.items():
            self.valid_data[key] = "1%s" % value
        
        # edit a barter item 
        self.barter_items_data['item-0-title'] = 'edited item'
        
        # add a barter item
        self.barter_items_data['item-5-title'] = 'new barter item'
        
        # update the barter item formset number
        self.barter_items_data['item-TOTAL_FORMS'] = 6
        
        # combine all dictionaries
        self.valid_data = dict(self.new_teacher_data.items() + self.new_course_data.items() + self.barter_items_data.items() + self.time_data.items())
        
        # post edited data to the form
        response = self.client.post(schedule_edit_url, data=self.valid_data, follow=True)

        # check that the schedule got saved correctly
        self.compare_schedule_to_data(response.context['schedule'])


    def test_schedule_feedback(self):
        """ Tests that the schedule-feedback page loads, that it's only
            possible to post feedback after a scheduled class had taken
            place, and that the submitted form is saved correctly.
        """
        # save a new schedule
        response = self.is_successful_submission(self.valid_data)        
        
        # new schedule object 
        schedule = response.context['schedule']
        
        # make sure schedule is 'pending'
        self.assertEqual(schedule.course_status, 0)
        
        # construct feedback url
        feedback_url = reverse('schedule-feedback', kwargs={'branch_slug' : self.branch.slug, 'schedule_slug' : schedule.slug, 'feedback_type' : 'student' })
        
        # load url
        response = self.client.get(feedback_url)
        
        # page should not load if the schedule is not approved
        self.assertEqual(response.status_code, 404)
        
        # approve schedule and save
        schedule.course_status = 3
        schedule.save()
        
        # loading the url again
        response = self.client.get(feedback_url)

        # if scheduled class didn't take place yet, the page should not load
        self.assertEqual(response.status_code, 404)
        
        # move the schedule to a time in the past
        now = datetime.utcnow().replace(tzinfo=utc) 
        schedule.start_time = now - timedelta(hours=47)
        schedule.end_time = now - timedelta(hours=48)
        schedule.save()
        
        # loading the url again
        response = self.client.get(feedback_url)
        
        # view should load now
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(self.branch.slug + '/schedule_feedback.html')
        
        # test an empty form submission
        response = self.client.post(feedback_url, data={}, follow=True)
        
        # an empty form should return 1 error for the required fields
        self.assertContains(response, 'Please', count=1)
        
        # post a valid form
        response = self.client.post(feedback_url, data={'content' : 'test feedback' }, follow=True)
        
        # check the form was submitted successfully
        self.assertRedirects(response, response.redirect_chain[0][0], response.redirect_chain[0][1])
        self.assertTemplateUsed(self.branch.slug + '/schedule_list.html')
        self.assertEqual(schedule.feedback_set.count(), 1)


    def tearDown(self):
        """ Delete branch files in case something went wrong 
            and the files weren't deleted.
        """
        # delete branches' files
        for branch in Branch.objects.all():
            branch.delete_files()