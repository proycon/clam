from django.db import models

class CLAMUsers( models.Model ):
        username = models.CharField( verbose_name='Username',max_length = 60, db_index = True,blank=False, unique=True)
        password = models.CharField( verbose_name='Password',max_length = 60 ,blank=False)
        fullname = models.CharField( verbose_name='Full name',max_length = 255 ,blank=False)
        institution = models.CharField( verbose_name='Institution',max_length = 255,blank=True )
        mail = models.CharField( verbose_name='E-Mail',max_length = 255, blank=False)
        active = models.BooleanField(default=0)
        
        

        
        
        
