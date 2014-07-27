import unittest
from google.appengine.api import mail
from google.appengine.ext import testbed

class MailTestCase(unittest.TestCase):

  def setUp(self):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_mail_stub()
    self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

  def tearDown(self):
    self.testbed.deactivate()

  def test_mail_sent(self):
    mail.send_mail(to='admin@maph4ck.com',
                   subject='Testing mail sent number 1',
                   sender='mail@maph4ck.com',
                   body='Still testing email sent')
    mail.send_mail(to='admin@maph4ck.com',
                   subject='Testing mail sent number 2',
                   sender='mail@maph4ck.com',
                   body='Still testing email sent')
    messages = self.mail_stub.get_sent_messages(to='admin@maph4ck.com')
    self.assertEqual(2, len(messages))
    self.assertEqual('admin@maph4ck.com', messages[0].to)