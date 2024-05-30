from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

def validate_image(data):
	"""
	Validate that the uploaded data is a valid image.
	"""
	image_format = imghdr.what(None, h=data)
	if not image_format:
		raise ValidationError('Invalid image format.')

class User(AbstractBaseUser, PermissionsMixin):
	pseudo = models.CharField(max_length=20, unique=True)
	email = models.EmailField(unique=True)
	avatar = models.BinaryField(validators=[validate_image])
	friends = models.ManyToManyField('self', through='Friendship')
	created_at = models.DateTimeField(auto_now_add=True)
	statistic = models.OneToOneField('Statistic', on_delete=models.CASCADE, null=True, blank=True, related_name='user_statistic')
	blocked_users = models.ManyToManyField('self', through='BlockedUser', symmetrical=False, related_name='blocking_users', blank=True)

	groups = models.ManyToManyField(
		'auth.Group',
		related_name='pong_user_set',  # Ajout de related_name unique
		blank=True,
		help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
		related_query_name='pong_user',
	)
	user_permissions = models.ManyToManyField(
		'auth.Permission',
		related_name='pong_user_set',  # Ajout de related_name unique
		blank=True,
		help_text='Specific permissions for this user.',
		related_query_name='pong_user',
	)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['email']

	def __str__(self):
		return self.pseudo

	def block_user(self, user):
		self.blocked_users.add(user)
		
	def unblock_user(self, user):
		self.blocked_users.remove(user)
		
	def is_blocked(self, user):
		return self.blocked_users.filter(id=user.id).exists()

class BlockedUser(models.Model):
	blocked_user = models.ForeignKey(User, related_name='blocked_by_users', on_delete=models.CASCADE)
	blocker = models.ForeignKey(User, related_name='blocked_users_set', on_delete=models.CASCADE)
	
	class Meta:
		unique_together = ('blocked_user', 'blocker')
	
	def __str__(self):
		return f"{self.blocker.pseudo} blocked {self.blocked_user.pseudo}"


class Chat(models.Model):
    name = models.CharField(max_length=255)
    participants = models.ManyToManyField('User', through='Participant', related_name='chats')
    messages = models.ManyToManyField('Message', related_name='chats', blank=True)

    def __str__(self):
        return self.name

class Participant(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='participants')
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE, related_name='chat_participants')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.pseudo} in {self.chat.name} ({"Admin" if self.is_admin else "Member"})'

class Message(models.Model):
    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.pseudo}: {self.content}'
	
def send_message(chat, sender, content):
    message = Message.objects.create(sender=sender, content=content)
    chat.messages.add(message)

    # Deliver the message to participants who haven't blocked the sender
    for participant in chat.participants.all():
        if not participant.is_blocked(sender):
            # Logic to deliver the message to the participant
            pass

class Friendship(models.Model):
	person1 = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE)
	person2 = models.ForeignKey(User, related_name='friends_of', on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = ('person1', 'person2')

	def __str__(self):
		return f"{self.person1.pseudo} is friends with {self.person2.pseudo}"

class Tournament(models.Model):
	name = models.CharField(max_length=100)
	winner = models.ForeignKey(User, related_name='won_tournaments', on_delete=models.CASCADE)
	participant1 = models.ForeignKey(User, related_name='participated_tournaments1', on_delete=models.CASCADE)
	participant2 = models.ForeignKey(User, related_name='participated_tournaments2', on_delete=models.CASCADE)
	participant3 = models.ForeignKey(User, related_name='participated_tournaments3', on_delete=models.CASCADE)
	participant4 = models.ForeignKey(User, related_name='participated_tournaments4', on_delete=models.CASCADE)

	def __str__(self):
		return f"Tournament name is {self.name} - winner is {self.winner}"

class Party(models.Model):
	game_name = models.CharField(max_length=100)
	game_time = models.DurationField(default=0)
	date = models.DateTimeField(auto_now_add=True)
	winner = models.ForeignKey(User, related_name='won_parties', on_delete=models.CASCADE)
	loser = models.ForeignKey(User, related_name='lost_parties', on_delete=models.CASCADE)
	tournament = models.ForeignKey(Tournament, related_name='parties', on_delete=models.SET_NULL, null=True, blank=True)

	def __str__(self):
		return f"Game name is {self.game_name} - {self.winner} vs {self.loser} on {self.date} at tournament {self.tournament.name}"

class Statistic(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistic_user')
	nbr_won_parties = models.IntegerField(default=0)
	nbr_lose_parties = models.IntegerField(default=0)
	total_time_played = models.DurationField(default=0)
	nbr_won_tournaments = models.IntegerField(default=0)

	def __str__(self):
		return f"Statistics for {self.user.pseudo} - won parties : {self.nbr_won_parties} - lose parties : {self.nbr_won_parties} - won tournament : {self.nbr_won_tournaments} - total time played : {self.total_time_played}"
