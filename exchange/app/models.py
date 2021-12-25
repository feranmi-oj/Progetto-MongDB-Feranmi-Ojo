from django.db import models
from djongo.models.fields import ObjectIdField
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Profile(models.Model):
	_id = ObjectIdField()
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	ips = models.Field(default=[],blank=True,null=True)
	subprofiles = models.Field(default={},blank=True,null=True)
	btc_amount = models.FloatField(default=0)
	usd_amount = models.FloatField(default=0)
	btc_balance = models.FloatField(default=0)
	usd_balance = models.FloatField(default=0)
	profit = models.FloatField(default=0)
	ip_address = models.CharField(max_length=150, blank=True, null=True)
	last_login = models.DateTimeField(default=timezone.now)
	def __str__(self):
		return "{}".format(self.user.username)




class Order(models.Model):
	_id = ObjectIdField()
	profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
	status = models.CharField(max_length=5)
	type = models.CharField(max_length=4)
	price = models.FloatField()
	quantity = models.FloatField()
	created = models.DateTimeField(auto_now_add=True)
	modified = models.DateTimeField(auto_now=True)

	def get_id(self):
		return self._id












