from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from base64 import b64encode
from django.core.files.base import ContentFile
from .utils import get_friends #, CustomPasswordChangeForm
from .models import NewUser, Tournament, Party, Chat, Message, Statistic, Participant, Friendship, BlockedUser, send_message, Invitation
from datetime import datetime
from django.db.models import Q, F
from django.db import IntegrityError
from django import forms
import pyotp
import qrcode
from io import BytesIO
import base64
import sys
import json
from django.http import JsonResponse
from datetime import timedelta
from django.contrib import messages
from django.template.loader import render_to_string
import logging
import re
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count

logger = logging.getLogger('pong')

# def index(request):
	# if not request.user.is_authenticated:
	#     return HttpResponseRedirect(reverse("login"))
	# return (render(request, "pong/homepage.html"))

def index(request) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return (JsonResponse({'html' : html,
								'url' :   reverse("login")
				}))
			return JsonResponse({'redirect' : reverse("login")})
		else :
			return HttpResponseRedirect(reverse("login"))
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/homepage_content.html", {}, request=request)
		return (JsonResponse({'html' : html,
							'url' :   reverse("index")
				}))
	else :
		return render(request, "pong/homepage.html")

# def login_view(request):
	# if not request.user.is_authenticated:
	#     return render(request,"pong/login.html")
	# else:
	#     #ça serait bien de rajouter une notification "vous êtes déjà connecté"
	#     return HttpResponseRedirect(reverse("index"))

def login_view(request):
	if request.user.is_authenticated:
		message = "Vous êtes déjà connecté"
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/homepage_content.html", {'message': message}, request)
			return (JsonResponse({'html' : html,
							'url' :   reverse("index")
				}))
		else:
			# Vous pouvez ajouter un message flash pour afficher la notification sur la page d'accueil.
			#messages.add_message(request, messages.INFO, message)
			return HttpResponseRedirect(reverse("index"))
	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html,
								'url' : reverse("login")
								})
		else:
			return render(request, "pong/login.html")



# def signup(request):
	# if request.user.is_authenticated:
	#     message = "Vous êtes déjà connecté"
	#     # if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#     #     return JsonResponse({'redirect': reverse("index"), 'message': message})
	#     # else:
	#         # Vous pouvez ajouter un message flash pour afficher la notification sur la page d'accueil.
	#     messages.add_message(request, messages.INFO, message)
	#     return HttpResponseRedirect(reverse("index"))
	# if request.method == "POST":
	#     email = request.POST.get("email")
	#     password = request.POST.get("password")
	#     confirm_password = request.POST.get("confirm_password")
	#     avatar = request.FILES.get("avatar")
	#     pseudo = request.POST.get("pseudo")

	#     if (confirm_password.casefold() != password.casefold()) :
	#         return render(request, 'pong/signup.html', {
	#             'error_message': "Password don't match, please try again."
	#         })

	#     if NewUser.objects.filter(pseudo=pseudo).exists():
	#         return render(request, 'pong/signup.html', {
	#             'error_message': "Username already exists. Please choose a different pseudo."
	#         })


	#     if NewUser.objects.filter(email=email).exists():
	#         return render(request, 'pong/signup.html', {
	#             'error_message': "Email already exists. Please choose a different email."
	#         })


	#     user = NewUser.objects.create_user(email=email, password=password, pseudo=pseudo, avatar=avatar)
	#     user.save()
	#     print(user.id)
	#     return HttpResponseRedirect(reverse("index"))
	# else:
	#     return render(request, "pong/signup.html")


def parsing_email(email) :
	if email :
		email = email.strip()
		try :
			index = email.index("@")
		except ValueError :
			logger.info("On passe ici exception")
			return ('')
		if ' ' in email :
			return ' '
		logger.info("oui oui")
		email_part = email[:index]
		domain_part = email[index+1:]
		logger.debug("email_part = %s", email_part)
		logger.debug("domain_part = %s", domain_part)
		if not email_part or '..' in email_part:
			return ''
		if not domain_part or '..' in domain_part:
			return ''
		if not (domain_part.endswith("com") or domain_part.endswith(".fr")) :
			return ('')
		email_invalid_chars = re.compile(r'[ !#\$%&\'\*\+\-/=\?\^_`\{\|\}~]')
		domain_invalid_chars = re.compile(r'[ !#\$%&\'\*\+\-/=\?\^_`\{\|\}~]')
		if email_invalid_chars.search(email_part) or domain_invalid_chars.search(domain_part):
			logger.info("Wrong char found !")
			return ''
	return (email)

def test_mail() :
	test_emails = [
		"example@'example.com",
		"example@example.fr",
		"example@ example.com",
		"example@example.c",
		"example@example.",
		" example@example.com ",
		"example@example..com",
		"example@example!.com"
	]

	for i,email in enumerate(test_emails):
		result = parsing_email(email)
		logger.debug("test n*%d retour fonction parsing = %s", i, result)


def validate_signup_data(email, password, confirm_password, pseudo):
	if not email :
		return "Email: this field can not be empty"
	if not password :
		return "Password: this field can not be empty"
	if not confirm_password :
		return "Confirm_password: this field can't be empty"
	if not pseudo:
		return "Pseudo: this field can't be empty"
	if confirm_password.casefold() != password.casefold():
		return "Password don't match, please try again."
	if NewUser.objects.filter(pseudo=pseudo).exists():
		return "Username already exists. Please choose a different pseudo."
	if NewUser.objects.filter(email=email).exists():
		return "Email already exists. Please choose a different email."
	return None


def signup(request):
	if request.user.is_authenticated:
		message = "Vous êtes déjà connecté"
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/homepage_content.html", {'message': message}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
								})
		else:
			#messages.add_message(request, messages.INFO, message)
			return HttpResponseRedirect(reverse("index"))

	if request.method == "POST":
		print("Nous passons bien ici oui")
		email = request.POST.get("email")
		password = request.POST.get("password")
		confirm_password = request.POST.get("confirm_password")
		avatar = request.FILES.get("avatar")
		pseudo = request.POST.get("pseudo")

		logger.debug("email avant parsing = %s", email)

		email = parsing_email(email)

		# test_mail()

		logger.debug("email apres parsing = %s", email)
		logger.debug("pseudo = %s", pseudo)
		logger.debug("password = %s", password)
		logger.debug("confirm_password = %s", confirm_password)


		error_message = validate_signup_data(email, password, confirm_password, pseudo)

		# logger.debug("error_message = %s", error_message)

		if error_message:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/signup_content.html", {'error_message': error_message}, request=request)
				return JsonResponse({'html': html,
									'url' : reverse("signup")
				})
			else:
				return render(request, 'pong/signup.html', {'error_message': error_message})

		user = NewUser.objects.create_user(email=email, password=password, pseudo=pseudo, avatar=avatar)
		# user.create_statistic()
		user.save()

		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))

	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			print("Nous passons bien ici 2")
			logger.info("html at ajax")
			html = render_to_string("pong/signup_content.html", {}, request=request)
			logger.debug("html in signup = %s", html)
			return JsonResponse({'html': html,
								'url' : reverse("signup")
			})
		else:
			return render(request, "pong/signup.html")



# def signin(request):
	# if request.user.is_authenticated:
	#     #ça serait bien de rajouter une notification "vous êtes déjà connecté"
	#     return HttpResponseRedirect(reverse("index"))
	# if request.method == "POST":
	#     email = request.POST.get("email")
	#     password = request.POST.get("password")
	#     user = authenticate(request, email=email, password=password)
	#     alerte = False
	#     if user is not None:
	#         # login(request, user)
	#         request.session['user_id'] = user.id
	#         if user.is_mfa_enabled is True:
	#             #send_otp(request)
	#             #request.session["email"] = email
	#             return redirect("otp")
	#         else:
	#             login(request, user)
	#             return HttpResponseRedirect(reverse("index"))
	#     else:
	#         alerte = True
	#         return render(request, "pong/signin.html", {
	#             "error_message" : alerte,
	#             "message": "Invalid credentials."
	#         })
	# else:
	#     return render(request, "pong/signin.html")




def handle_authentication(request, email, password):
	logger.info("__ D")
	user = authenticate(request, email=email, password=password)
	print("email =", email, "password =", password)
	if user is not None:
		logger.info("__ E")
		request.session['user_id'] = user.id
		user.is_active_status = True
		user.save()
		logger.debug("user = %s", user)
		if user.is_mfa_enabled:
			return {'redirect': "pong/otp_content.html",
					'url' : reverse("otp")
			}
		else:
			login(request, user)
			return {'redirect': "pong/homepage_content.html",
					'url' : reverse("index")
			}
	else:
		logger.info("__ F")
		logger.info("l'utilisateur est null")
		return {'error_message': "Invalid credentials."}

def signin(request):
	logger.info("__ A")
	if request.user.is_authenticated:
		logger.info("__ B")
		message = "Vous êtes déjà connecté"
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/homepage_content.html", {'message': message}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			#messages.add_message(request, messages.INFO, message)
			return HttpResponseRedirect(reverse("index"))

	if request.method == "POST":
		logger.info("__ C")
		email = request.POST.get("email")
		password = request.POST.get("password")

		result = handle_authentication(request, email, password)

		logger.debug("email = %s", email)
		logger.debug("password = %s", password)

		if 'error_message' in result:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/signin_content.html", {'error_message': True, 'message': result['error_message']}, request=request)
				return JsonResponse({'html': html,
									'url' : reverse("signin")
				})
			else:
				return render(request, "pong/signin.html", {"error_message": True, "message": result['error_message']})
		else:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string(result['redirect'], {}, request=request)
				return JsonResponse({'html': html,
									'url' : result['url']
				})
			else:
				new_url = result['redirect']
				new_url = new_url.replace("_content", "")
				return HttpResponseRedirect(new_url)

	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/signin_content.html", {}, request=request)
			logger.debug("html in sigin = %s", html)
			return JsonResponse({'html': html,
								'url': reverse("signin")
			})
		else:
			return render(request, "pong/signin.html")

#faire la ologique du otp sur la view otp avec la comparaison du code que le mec aura recu (comme il a deja scanné)
# def otp_view(request):
#     user = NewUser.objects.get(id=(request.session.get('user_id')))
#     message = 'nothing'
#     value = False
#     if request.method == "POST":
#         otp = request.POST["otp"]
#         totp = pyotp.TOTP(user.mfa_hash) #check the secret key
#         if totp.verify(otp): # the case where we can login the user
#             login(request, user)
#             return HttpResponseRedirect(reverse("index"))
#         else: # le cas où la secret key n'est pas la bonne
#             value = True
#             message = 'invalid one time password or the password has expired'
#     return render(request, 'pong/otp.html' , {
#                                                 'error_message' : {
#                                                                         'value' : value,
#                                                                         'message' : message
#                                                                 }
#                                             })

def otp_view(request):
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	message = 'nothing'
	value = False
	if request.method == "POST":
		otp = ''.join([request.POST.get(f'otp_{i}') for i in range(6)])  # Récupère chaque chiffre du OTP
		totp = pyotp.TOTP(user.mfa_hash)  # Initialise TOTP avec le hachage MFA de l'utilisateur
		if totp.verify(otp):  # Vérifie si le OTP est correct
			login(request, user)  # Connecte l'utilisateur
			#return HttpResponseRedirect(reverse("index"))  # Redirige vers la page d'accueil
			html = render_to_string("pong/homepage_content.html", {}, request=request)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'html': html,
								'url' : reverse("index")
				})
			else :
				return render(request, 'pong/otp.html' , {
												'error_message' : {
																		'value' : value,
																		'message' : message
																}
											})
		else:
			value = True
			message = 'invalid one time password or the password has expired'
			html = render_to_string("pong/otp_content.html", {'error_message': {
					'value': value,
					'message': message
				}}, request=request)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				return JsonResponse({'html': html,
								'url' : reverse('otp')
					})
			else :
				return render(request, 'pong/otp.html' , {
												'error_message' : {
																		'value' : value,
																		'message' : message
																}
											})

	return render(request, "pong/otp.html")

def build_history(user, partie) :
	history = []
	for game in partie :
		winner = game.winner.pseudo.strip()
		loser = game.loser.pseudo.strip()
		if ((user.pseudo == winner) or (user.pseudo == loser)) :
			history.append(game)
	return (history)

def update_stats_other_profile(user, partie, name) :
	user_statistic = None
	logger.info("On passe la ouai")
	user_statistic, created = Statistic.objects.get_or_create(user=user)
	data = {'user_statistic' : None,
			'history' : []}
	if created:
		user.statistic = user_statistic
		user.save()
	logger.debug("user = %s", user)
	logger.debug("statistics = %s", user.statistic)
	history = build_history(user, partie)
	data['history'] = history
	if name == "pong" :
		nbr_won_parties = Party.objects.filter((Q(user_red=user) | Q(user_blue=user)) & Q(winner=user) & Q(game_name="pong")).count()
		logger.debug("nbr_won_parties_ = %d", nbr_won_parties)
		if (nbr_won_parties) :
			user_statistic.nbr_won_parties = nbr_won_parties
		nbr_lost_parties = Party.objects.filter((Q(user_red=user) | Q(user_blue=user)) & Q(loser=user) & Q(game_name="pong")).count()
		logger.debug("nbr_lost_parties_ = %d", nbr_lost_parties)
		if (nbr_lost_parties) :
			user_statistic.nbr_lose_parties = nbr_lost_parties
		nbr_won_tournaments = Tournament.objects.filter(winner=user).count()
		logger.debug("nbr_lost_parties_ = %d", nbr_lost_parties)
		if (nbr_won_tournaments) :
			user_statistic.nbr_won_tournaments = nbr_won_tournaments
	if name == "tic":
		# Comptage des parties nulles
		nbr_draw_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			score_red=0,
			score_blue=0,
			game_name="tic"
		).count()
		logger.debug("nbr_draw_parties = %d", nbr_draw_parties)
		if nbr_draw_parties:
			user_statistic.nbr_draw = nbr_draw_parties

		# Comptage des parties gagnées
		nbr_won_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			winner=user,
			game_name="tic"
		).exclude(
			Q(score_red=0) & Q(score_blue=0)
		).count()
		logger.debug("nbr_won_parties = %d", nbr_won_parties)
		if nbr_won_parties:
			user_statistic.nbr_won_parties = nbr_won_parties

		# Comptage des parties perdues
		nbr_lost_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			loser=user,
			game_name="tic"
		).exclude(
			Q(score_red=0) & Q(score_blue=0)
		).count()
		logger.debug("nbr_lost_parties = %d", nbr_lost_parties)
		if nbr_lost_parties:
			user_statistic.nbr_lose_parties = nbr_lost_parties

	logger.debug("user stats = %s", user_statistic)
	game_duration = timedelta()
	user_statistic.total_time_played = timedelta(0)
	for i in range(len(history)):
		game_duration += history[i].game_time
		if user_statistic :
			logger.info("Ici oui")
			logger.debug("time = %s", history[i].game_time)
			user_statistic.total_time_played += history[i].game_time
			logger.debug("time 2 = %s", user_statistic.total_time_played)
	user.statistic = user_statistic
	user.save()
	data['user_statistic'] = user_statistic
	logger.debug("data = %s", data)
	return (data)



def update_stats(user, partie, name) :
	user_statistic = None
	# if not user.statistic:
	data = {
		'history' : [],
		'user_statistic' : None,
		'game_dates_json': [],
		'game_results_json': [],
		'game_duration_json' : {},
		'is_tic' : False
	}
	logger.info("On passe la ouai")
	user_statistic, created = Statistic.objects.get_or_create(user=user)
	if created:
		user.statistic = user_statistic
		user.save()
		# user_statistic.nbr_won_parties += 1#
	logger.debug("parties = %s", partie)
	logger.debug("user = %s", user)
	logger.debug("statistics = %s", user.statistic)
	history = build_history(user, partie)
	data['history'] = history
	if name == "pong" :
		nbr_won_parties = Party.objects.filter((Q(user_red=user) | Q(user_blue=user)) & Q(winner=user) & Q(game_name="pong")).count()
		logger.debug("nbr_won_parties_ = %d", nbr_won_parties)
		if (nbr_won_parties) :
			user_statistic.nbr_won_parties = nbr_won_parties
		nbr_lost_parties = Party.objects.filter((Q(user_red=user) | Q(user_blue=user)) & Q(loser=user) & Q(game_name="pong")).count()
		logger.debug("nbr_lost_parties_ = %d", nbr_lost_parties)
		if (nbr_lost_parties) :
			user_statistic.nbr_lose_parties = nbr_lost_parties
		nbr_won_tournaments = Tournament.objects.filter(winner=user).count()
		logger.debug("nbr_lost_parties_ = %d", nbr_lost_parties)
		if (nbr_won_tournaments) :
			user_statistic.nbr_won_tournaments = nbr_won_tournaments
	if name == "tic":
		# Comptage des parties nulles
		nbr_draw_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			score_red=0,
			score_blue=0,
			game_name="tic"
		).count()
		logger.debug("nbr_draw_parties = %d", nbr_draw_parties)
		if nbr_draw_parties:
			user_statistic.nbr_draw = nbr_draw_parties

		# Comptage des parties gagnées
		nbr_won_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			winner=user,
			game_name="tic"
		).exclude(
			Q(score_red=0) & Q(score_blue=0)
		).count()
		logger.debug("nbr_won_parties = %d", nbr_won_parties)
		if nbr_won_parties:
			user_statistic.nbr_won_parties = nbr_won_parties

		# Comptage des parties perdues
		nbr_lost_parties = Party.objects.filter(
			Q(user_red=user) | Q(user_blue=user),
			loser=user,
			game_name="tic"
		).exclude(
			Q(score_red=0) & Q(score_blue=0)
		).count()
		logger.debug("nbr_lost_parties = %d", nbr_lost_parties)
		if nbr_lost_parties:
			user_statistic.nbr_lose_parties = nbr_lost_parties

		data['is_tic'] = True
	logger.debug("user stats = %s", user_statistic)
	game_date = []
	game_result = []
	game_result_numeric = []
	for game in history :
		game_date.append(game.date.strftime('%Y-%m-%d'))
		if (game.winner.pseudo == user.pseudo) :
			game_result.append('Victory')
		elif (game.loser.pseudo == user.pseudo) :
			game_result.append('Defeat')
	for result in game_result :
		if (result == "Victory") :
			game_result_numeric.append(1)
		else :
			game_result_numeric.append(-1)
	days_of_playing = {}
	game_duration = timedelta()
	user_statistic.total_time_played = timedelta(0)
	for i in range(len(history)):
		game_duration += history[i].game_time
		if user_statistic :
			logger.info("Ici oui")
			logger.debug("time = %s", history[i].game_time)
			user_statistic.total_time_played += history[i].game_time
			logger.debug("time 2 = %s", user_statistic.total_time_played)

		if ((i == len(history) - 1) or (history[i].date.strftime('%Y-%m-%d') != history[i + 1].date.strftime('%Y-%m-%d'))) :
			days_of_playing[history[i].date.strftime('%Y-%m-%d')] = game_duration.total_seconds()
			game_duration = timedelta()
	user.statistic = user_statistic
	user.save()
	data['user_statistic'] = user_statistic
	data['game_dates_json'] = json.dumps(game_date)
	data['game_results_json'] = json.dumps(game_result_numeric)
	data['game_duration_json'] = json.dumps(days_of_playing)
	logger.debug("data = %s", data)
	return (data)


def statistics_pong(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	data = {}
	partys_pong = Party.objects.filter(game_name="pong")
	if partys_pong.exists() :
		data = update_stats(user, partys_pong, "pong")
	logger.debug("Data pong = %s", data)
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/statistics_pong_content.html", {
																		'user' : user,
																		'data' : data
																	}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("statistics_pong")
			})
	else :
		return render(request, "pong/statistics_pong.html", {
													'user' : user,
													'data' : data
													})


def statistics_tic(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	data = {'is_tic' : True}
	partys_tic = Party.objects.filter(game_name="tic")
	if partys_tic.exists():
		data = update_stats(user, partys_tic, "tic")
	logger.debug("Data tic = %s", data)
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/statistics_pong_content.html", {
																		'user' : user,
																		'data' : data
																	}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("statistics_tic")
			})
	else :
		return render(request, "pong/statistics_pong.html", {
													'user' : user,
													'data' : data
													})


def statistics(request) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/statistics_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("statistics")
			})
	else :
		return render(request, "pong/statistics.html", {})


def chat_solo(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	chats = Chat.objects.all() #if none
	message_block = None
	message_invitation = None
	message_unblock = None
	if not chats :
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/add_chat_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("add_chat")
			})
		else:
			return HttpResponseRedirect(reverse("add_chat"))
	list_of_chats = []
	for chat in chats :
		participants = chat.participants.all()
		for participant in participants :
			logger.debug("user participants = %s", participant)
			if (participant.pseudo == user.pseudo) :
				list_of_chats.append((chat))
	if not list_of_chats :
		list_of_chats = get_list_of_potential_chats(user, chats)
		logger.debug("list de chat dans chat_room = %s", list_of_chats)
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/join_chat_content.html", {'chat_info': {
																					'list_of_chats' : list_of_chats}}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("join_chat")
			})
		else:
			return HttpResponseRedirect(reverse("join_chat"))
	chat_info = {'list_of_chats' : list_of_chats}
	message_info = {}
	toggle = True
	# logger.debug("list of chat = %s", list_of_chats)
	for chat in reversed(list_of_chats) :
		messages = chat.messages.all()
		message_info[chat.name] = []
		for message in messages :
			toggle = is_blocked(user, message.sender)
			logger.debug("toggle = %s", toggle)
			if not toggle :
				logger.info("la condition est remplie")
				message_info[chat.name].append({
					'message' : message.content,
					'sender' : message.sender.pseudo,
					'time' : message.timestamp.isoformat(),
					})
		name_chat = chat.name
		break

	context = {'chat_info' : chat_info,
				'message_info' : json.dumps(message_info),
				'chat_name' : name_chat,
				'chat_name_json' : json.dumps({'chat_name' : name_chat}),
				'message_block' : message_block,
				'message_invitation' : message_invitation,
				'is_solo' : True,
				'message_unblock' : message_unblock,
				'user' : user.pseudo
	}
	if request.method == 'POST' :
		if request.POST.get('user_target') :
			logger.info("Oui c'est bon")
			user_target = request.POST.get('user_target')
			all_users = NewUser.objects.all()
			# message = None
			found = False
			for founded in all_users :
				if (user_target == founded.pseudo) :
					if founded.pseudo == user.pseudo :
						message_block = "You can't block yourself"
					else :
						found = True
					break
			if found :
				target = NewUser.objects.get(pseudo=user_target)
				if target :
					BlockedUser.objects.create(blocker=user, blocked_user=target)
					message_block = f"{user_target} has been blocked"
			elif not found and not message_block :
				message_block = f"{user_target} doesn't exist"
			if message_block :
				context['message_block'] = message_block
			# chat_name_url = None
			# if chat_name :
			# 	chat_name_url = chat_name
			# else:
			chat_name_url = name_chat
			logger.debug("context = %s", context)
			BlockedUser_all = BlockedUser.objects.all()
			logger.debug("BlockedUser_all = %s", BlockedUser_all)
		if request.POST.get("invit") :
			logger.info("On rentre bien dans l'invitation")
			logger.debug("ctxt1 = %s", context)
			other_user = request.POST.get("invit")
			if other_user == user.pseudo:
				context['message_invitation'] = "You cannot invit yourself"
				logger.debug("ctxt2 = %s", context)
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/chat_content.html", context, request=request)
					return JsonResponse({'html': html,
							'url' : reverse("chat_solo")
					})
				else:
					return render(request, "pong/chat.html", context)
			try :
				receiver = NewUser.objects.get(pseudo=other_user)
				logger.debug("receiver = %s", receiver)
				try :
					logger.info("\n-----------")
					logger.debug("user= %s", user)
					logger.debug("receiver = %s", receiver)
					invitation = Invitation.objects.get(sender=user, receiver=receiver)
					message_invitation = f"Invitation was already sended to {receiver.pseudo}"
					context['message_invitation'] = message_invitation
				except ObjectDoesNotExist :
					logger.info("On rentre ici malgre tout")
					invitation = Invitation.objects.create(sender=user, receiver=receiver)
					message_invitation = f"Invitation was sended to {receiver.pseudo}"
					context['message_invitation'] = message_invitation
					invitation.save()
			except ObjectDoesNotExist :
				message_invitation = "User doesn't exist"
				context['message_invitation'] = message_invitation
			logger.debug("ctxt3 = %s", context)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : reverse("chat_solo")
					})
			else:
				return render(request, "pong/chat.html", context)
		if request.POST.get("unblock") :
			unblock_user_pseudo = request.POST.get("unblock")
			check = is_in_users(unblock_user_pseudo)
			if check :
				user_target = NewUser.objects.get(pseudo=unblock_user_pseudo)
				error_message = unblock_user(user, user_target)
			else :
				error_message = f"{unblock_user_pseudo} doesn't exist"
			context['message_unblock'] = error_message
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : reverse("chat_solo")
					})
			else:
				return render(request, "pong/chat.html", context)
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/chat_content.html", context, request=request)
		return JsonResponse({'html': html,
								'url' : reverse("chat_solo")
			})
	else:
		return render(request, "pong/chat.html", context)

def looking_for_invitation(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))

	user = request.user
	try:
		invitation = Invitation.objects.get(receiver=user)

		if user.in_waiting_pong or user.in_waiting_tic:
			return JsonResponse({
				'status': False,
				'wait': True
			})
		return JsonResponse({
			'status': True,
			'opponent': invitation.sender.pseudo,
		})
	except ObjectDoesNotExist:
		return JsonResponse({
			'status': False,
		})

def invitation_response(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = request.user
	if request.method == 'POST':
		accept = request.POST.get("accept")
		try:
			other_user = NewUser.objects.get(pseudo=request.POST.get("opponent"))
		except ObjectDoesNotExist:
			return JsonResponse({})
		try:
			invit = Invitation.objects.get(sender=other_user, receiver=user)
		except ObjectDoesNotExist:
			logger.info("invit nothing")
			return JsonResponse({})
		if invit:
			invit.delete()
		if accept == "1":
			party = Party.objects.create(winner=user, loser=other_user, user_red=user, user_blue=other_user, game_name='pong', game_time=timedelta(minutes=0))
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/pong_page_content.html", {
					'party_end': party.is_ended,
					'party_id': party.id,
					'user_red': party.user_red.pseudo,
					'user_blue': party.user_blue.pseudo,
					'id_red': party.user_red.id,
					'id_blue': party.user_blue.id,
				}, request=request)
				return JsonResponse({'html': html, 'url' : reverse("pong_page", args=[party.id]) })
			else:
				return render(request, 'pong/pong_page.html', {
					'party_end': party.is_ended,
					'party_id': party.id,
					'user_red': party.user_red.pseudo,
					'user_blue': party.user_blue.pseudo,
					'id_red': party.user_red.id,
					'id_blue': party.user_blue.id,
				})
	return JsonResponse({})


def looking_for_tournament(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	not_full_tournaments = Tournament.objects.filter(
		Q(participant1__isnull=True) |
		Q(participant2__isnull=True) |
		Q(participant3__isnull=True) |
		Q(participant4__isnull=True)
	).last()

	if not_full_tournaments:
		return JsonResponse({
			'status': True,
		})
	else:
		return JsonResponse({
			'status': False,
		})

def chat_room(request, chat_name):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	chats = Chat.objects.all() #if none
	message_block = None
	message_invitation = None
	message_unblock = None
	if not chats :
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/add_chat_content.html", {'chat_info' : {
																					'value' : True,
																					'list_of_chats' : list_of_chats,
																				}}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("add_chat")
			})
		else:
			return HttpResponseRedirect(reverse("add_chat"))
	list_of_chats = []
	for chat in chats :
		participants = chat.participants.all()
		for participant in participants :
			logger.debug("user participants = %s", participant)
			if (participant.pseudo == user.pseudo) :
				list_of_chats.append((chat))
	if not list_of_chats :
		list_of_chats = get_list_of_potential_chats(user, chats)
		logger.debug("list de chat dans chat_room = %s", list_of_chats)
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/join_chat_content.html", {'chat_info': {
																					'list_of_chats' : list_of_chats}}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("join_chat")
			})
		else:
			return HttpResponseRedirect(reverse("join_chat"))
	# logger.debug("list of chat = %s", list_of_chats)
	chat_info = {'list_of_chats' : list_of_chats}
	message_info = {}
	context = {'chat_info' : None,
					'message_info' : None,
					'chat_name' : None,
					'chat_name_json' : None,
					'message_block' : message_block,
					'message_invitation' : message_invitation,
					'is_solo' : False,
					'message_unblock' : None,
					'user' : user.pseudo
		}
	if not chat_name :
		logger.info("On rentre ici dans la vue chat_room")
		for chat in reversed(list_of_chats) :
			messages = chat.messages.all()
			message_info[chat.name] = []
			for message in messages :
				message_info[chat.name].append({
					'message' : message.content,
					'sender' : message.sender.pseudo,
					'time' : message.timestamp.isoformat(),
				})
			name_chat = chat.name
			break
		context['chat_info'] = chat_info
		context['message_info'] = json.dumps(message_info)
		context['chat_name'] = name_chat
		context['chat_name_json'] = json.dumps({'chat_name' : name_chat})
	else :
		logger.info("Tout va bien on passe la ")
		toggle = True
		for chat in reversed(list_of_chats) :
			if (chat.name == chat_name) :
				messages = chat.messages.all()
				message_info[chat.name] = []
				for message in messages :
					# blocked_object = BlockedUser.objects.all()
					# blocked_list = []
					# if blocked_object :
					# 	for blocked in blocked_object :
					# 		if user.pseudo == blocked.blocker.pseudo :
					# 			if message.sender == blocked.blocked.pseudo :
					# 				toggle = False
					toggle = is_blocked(user, message.sender)
					logger.debug("toggle = %s", toggle)
					if not toggle :
						logger.info("la condition est remplie")
						message_info[chat.name].append({
							'message' : message.content,
							'sender' : message.sender.pseudo,
							'time' : message.timestamp.isoformat(),
						})

				break
			# context = {'chat_info' : chat_info,
			# 			'message_info' : json.dumps(message_info),
			# 			'chat_name' : chat_name,
			# }
		context['chat_info'] = chat_info
		context['message_info'] = json.dumps(message_info)
		context['chat_name'] = chat_name
		context['chat_name_json'] = json.dumps({'chat_name' : chat_name})
		logger.debug("context = %s", context)
	if request.method == "POST" :
		if request.POST.get("message_content") :
			message_content = request.POST.get("message_content")
			logger.debug("message_content = %s", message_content)
			logger.debug("context = %s", context)
			# chat_id = request.POST.get('chat_id')
			# logger.debug("chat_id = %s", chat_id)
			# chat = get_object_or_404(Chat, id=chat_id)
			# logger.debug("chat = %s", chat)
			chat_name_url = None
			if chat_name :
				chat_name_url = chat_name
			else:
				chat_name_url = name_chat
			chat_object = Chat.objects.get(name=chat_name_url)
			logger.debug("chat_objet = %s", chat_object)
			message_object = Message.objects.create(sender=user, content=message_content)
			message_object.save()
			send_message(chat_object, message_object)
			chat_object.save()
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : (f"{chat_name_url}")
					})
				return render(request, "pong/chat.html", context)
		if request.POST.get('user_target') :
			logger.info("Oui c'est bon")
			user_target = request.POST.get('user_target')
			if not user_target :
				logger.info("On passe par ce chemin")
				message = " Error : Field Empty"
				context['message_block'] = message
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/chat_content.html", context, request=request)
					return JsonResponse({'html': html,
											'url' : (f"{chat_name_url}")
						})
				else:
					return render(request, "pong/chat.html", context)
			logger.debug("user_target = %s", user_target)
			all_users = NewUser.objects.all()
			message = None
			found = False
			for founded in all_users :
				if (user_target == founded.pseudo) :
					if founded.pseudo == user.pseudo :
						message = "You can't block yourself"
					else :
						found = True
					break
			if found :
				target = NewUser.objects.get(pseudo=user_target)
				if target :
					BlockedUser.objects.create(blocker=user, blocked_user=target)
					message_block = f"{user_target} has been blocked"
			elif not found and not message :
				message = f"{user_target} doesn't exist"
			if message :
				context['message_block'] = message
			chat_name_url = None
			if chat_name :
				chat_name_url = chat_name
			else:
				chat_name_url = name_chat
			logger.debug("message_block = %s", context['message_block'])
			logger.debug("context = %s", context)
			BlockedUser_all = BlockedUser.objects.all()
			logger.debug("BlockedUser_all = %s", BlockedUser_all)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : (f"{chat_name_url}")
					})
			else:
				return render(request, "pong/chat.html", context)
		if request.POST.get("invit") :
			logger.info("On rentre bien dans l'invitation")
			other_user = request.POST.get("invit")
			if other_user == user.pseudo:
				chat_name_url = None
				if chat_name :
					chat_name_url = chat_name
				else:
					chat_name_url = name_chat
				context['message_invitation'] = "You cannot invit yourself"
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/chat_content.html", context, request=request)
					return JsonResponse({'html': html,
						'url' : (f"{chat_name_url}")
					})
				else:
					return render(request, "pong/chat.html", context)
			try :
				receiver = NewUser.objects.get(pseudo=other_user)
				logger.debug("receiver = %s", receiver)
				try :
					logger.debug("user= %s", user)
					logger.debug("receiver = %s", receiver)
					invitation = Invitation.objects.get(sender=user, receiver=receiver)
					message_invitation = f"Invitation was already sended to {receiver.pseudo}"
					context['message_invitation'] = message_invitation
				except ObjectDoesNotExist :
					logger.info("On rentre ici malgre tout")
					invitation = Invitation.objects.create(sender=user, receiver=receiver)
					message_invitation = f"Invitation was sended to {receiver.pseudo}"
					logger.debug("invitation = %s", invitation)
					context['message_invitation'] = message_invitation
					invitation.save()
			except ObjectDoesNotExist :
				message_invitation = "User doesn't exist"
				context['message_invitation'] = message_invitation
			chat_name_url = None
			if chat_name :
				chat_name_url = chat_name
			else:
				chat_name_url = name_chat
			logger.debug("ctxt = %s", context)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : (f"{chat_name_url}")
					})
			else:
				return render(request, "pong/chat.html", context)
		if request.POST.get("unblock") :
			unblock_user_pseudo = request.POST.get("unblock")
			check = is_in_users(unblock_user_pseudo)
			if check :
				user_target = NewUser.objects.get(pseudo=unblock_user_pseudo)
				error_message = unblock_user(user, user_target)
			else :
				error_message = f"{unblock_user_pseudo} doesn't exist"
			context['message_unblock'] = error_message
			chat_name_url = None
			if chat_name :
				chat_name_url = chat_name
			else:
				chat_name_url = name_chat
			logger.debug("ctxt = %s", context)
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/chat_content.html", context, request=request)
				return JsonResponse({'html': html,
										'url' : (f"{chat_name_url}")
					})
			else:
				return render(request, "pong/chat.html", context)
	else:
		chat_name_url = None
		if chat_name :
			chat_name_url = chat_name
		else:
			chat_name_url = name_chat
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/chat_content.html", context, request=request)
			return JsonResponse({'html': html,
									'url' : (f"{chat_name_url}")
				})
		return render(request, "pong/chat.html", context)


def extract_blocked_list(user, user_friends) :
	blocked_object = BlockedUser.objects.all()
	blocked_list = []
	if blocked_object :
		for blocked in blocked_object :
			if user.pseudo == blocked.blocker.pseudo:
				for friend in user_friends :
					if friend.pseudo == blocked.blocked_user.pseudo :
						blocked_list.append(friend)
	return blocked_list

def extract_user_blocked_by_other(user, user_friends) :
	blocked_object = BlockedUser.objects.all()
	blocked_by = []
	if blocked_object :
		for blocked in blocked_object :
			if user.pseudo == blocked.blocked_user.pseudo:
				for friend in user_friends :
					if friend.pseudo == blocked.blocker.pseudo :
						blocked_by.append(friend)
	return blocked_by

def set_info_chat(user, user_friends, info_add_chat) :
	blocked_list = extract_blocked_list(user, user_friends)
	blocked_by = extract_user_blocked_by_other(user, user_friends)
	if blocked_list or blocked_by:
		for friend in user_friends :
			if friend not in blocked_list and friend not in blocked_by :
				info_add_chat['users_ok'].append(friend)
		if blocked_list :
			info_add_chat['blocked_users'] = blocked_list
		if blocked_by :
			info_add_chat['blocked_by'] = blocked_by
	else :
		for friend in user_friends :
			info_add_chat['users_ok'].append(friend)
	return info_add_chat

def check_private_possibility(user) :
	user_friends = get_friends(user)
	info_add_chat = {
		'token' : None,
		'users_ok' : [],
		'blocked_users' : [],
		'blocked_by' : []
	}
	if not user_friends :
		info_add_chat['token'] = False
		return info_add_chat
	info_add_chat = set_info_chat(user, user_friends, info_add_chat)
	info_add_chat['token'] = True
	logger.debug("info_add_chat = %s", info_add_chat)
	return (info_add_chat)

def is_in_users(username) :
	# error_message = None
	toggle = False
	all_users = NewUser.objects.all()
	for user_solo in all_users :
		if username == user_solo.pseudo :
			toggle = True
			break
	if not toggle :
		return (None)
	return user_solo

def is_in_friends_list(username, friend_list) :
	toggle = False
	error_message = None
	for friend in friend_list :
		if friend.pseudo == username :
			toggle = True
			break
	if not toggle :
		error_message = f"{username} is not your friend"
	return (error_message)

def is_blocked_add_chat(username, blocked_list) :
	toggle = False
	error_message = None
	for blocked in blocked_list :
		logger.debug("blocked.pseudo = %s", blocked.pseudo)
		logger.debug("username = %s", username)
		if blocked.pseudo == username :
			toggle = True
			break
	if toggle :
		error_message = f"{username} is blocked"
	# logger.debug("blocked_list = %s", blocked_list)
	# # if username in blocked_list :
	return (error_message)

def is_blocked_by_other_add_chat(username, blocked_by) :
	toggle = False
	error_message = None
	for blocked in blocked_by :
		logger.debug("blocked.pseudo = %s", blocked.pseudo)
		logger.debug("username = %s", username)
		if blocked.pseudo == username :
			toggle = True
			break
	if toggle :
		error_message = f"{username} has blocked you"
	# logger.debug("blocked_by = %s", blocked_by)
	# # if username in blocked_by :
	return (error_message)


def is_blocked(user, target) :
	blocked_object = BlockedUser.objects.all()
	if blocked_object :
		for block in blocked_object :
			if block.blocker.pseudo == user.pseudo and block.blocked_user.pseudo == target.pseudo :
				return (True)
	return False


def unblock_user(user, user_target):
	verif = is_blocked(user, user_target)
	error_message = None
	if verif:
		blocked_object = BlockedUser.objects.filter(blocker=user, blocked_user=user_target).first()
		if blocked_object:
			blocked_object.delete()
			error_message = f"{user_target.pseudo} is unblocked"
		else:
			error_message = f"Error: {user_target.pseudo} is not in your blocked user list"
	else:
		error_message = f"Error: {user_target.pseudo} is not in your blocked user list"
	return error_message



# def block_user(request) :
# 	if request.method == 'POST' :
# 		logger.info("Oui c'est bon")
# 		user = NewUser.objects.get(id=(request.session.get('user_id')))
# 		user_target = request.POST.get('user_target')
# 		all_users = NewUser.objects.all()
# 		message = None
# 		found = False
# 		for user in all_users :
# 			if (user_target == user.pseudo) :
# 				found = True
# 				break
# 		if found :
# 			BlockedUser.objects.create(blocker=user, blocked_user=user_target)
# 			message = f"{user_target} has been blocked"
# 		else :
# 			message = f"{user_target} doesn't exist"
# 		logger.debug("message = %s", message)
# 		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
# 			return JsonResponse({'message' : message})
# 		else:
# 			return redirect('chat')
# 	else :
# 		response_data = {'error': 'Invalid request method'}
# 		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
# 			return JsonResponse(response_data)
# 		else:
# 			return redirect('chat')

def add_chat(request) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	private_possibility = False
	add_chat_info = check_private_possibility(user)
	if request.method == "POST" :
		if (request.POST.get("chat_name")) :
			chat_name = request.POST.get("chat_name")
			logger.debug("chat_name = %s", chat_name)
			chats = Chat.objects.all()
			logger.debug("chats = %s", chats)
			error_message = None
			for chat in chats :
				logger.debug("chat_name for = %s", chat_name)
				logger.debug("chat.name = %s", chat.name)
				if (chat_name == chat.name) :
					logger.info("Je rentre dedans")
					error_message = "Chat already exist. Please try with another one"
					break
			if (error_message) :
				logger.info("Je rentre dans error_message")
				logger.debug("error_message = %s", error_message)
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_chat_content.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info
																		}, request=request)
					return JsonResponse({'html': html,
										'url' : reverse("add_chat")
					})
				else:
					return render(request, "pong/add_chat.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info})
			chat, created = Chat.objects.get_or_create(name=chat_name)
			user_participant, created = Participant.objects.get_or_create(user=user, chat=chat)
			chat.save()
			user_participant.save()
			error_message = f"Chat {chat_name} was created successfully"
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_chat_content.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info}, request=request)
					return JsonResponse({'html': html,
										'url' : reverse("add_chat")
					})
			else:
				return render(request, "pong/add_chat.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info})
		if request.POST.get("private_chat") :
			logger.info("On se retrouve bien ici")
			friend_name = request.POST.get("private_chat")
			logger.debug("friend_name = %s", friend_name)
			logger.debug("friend_name = %s", type(friend_name))
			error_message = None
			other_user = is_in_users(friend_name)
			if not other_user :
				error_message = f"{friend_name} user doesn't exist"
			if not error_message :
				friend_list = get_friends(user)
				logger.debug("friend_list = %s", friend_list)
				error_message = is_in_friends_list(friend_name, friend_list)
				if not error_message :
					error_message = is_blocked_add_chat(friend_name, add_chat_info['blocked_users'])
					if not error_message :
						error_message = is_blocked_by_other_add_chat(friend_name, add_chat_info['blocked_by'])
						if not error_message :
							error_message = "Tous les filtres ont ete passes"
							chat_name = other_user.pseudo + " et " + user.pseudo
							chat_private, created = Chat.objects.get_or_create(name=chat_name, is_private=True)
							participant1, created = Participant.objects.get_or_create(user=user, chat=chat_private)
							participant2, created = Participant.objects.get_or_create(user=other_user, chat=chat_private)
							chat_private.save()
							participant1.save()
							participant2.save()
							error_message =  f"You are now in private conversation with {other_user.pseudo}"
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_chat_content.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info}, request=request)
					return JsonResponse({'html': html,
										'url' : reverse("add_chat")
					})
			else:
				return render(request, "pong/add_chat.html", {'message': {
																		'value' : True,
																		'error_message' : error_message},
																		'add_chat_info' : add_chat_info})
	else :
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/add_chat_content.html", {'add_chat_info' : add_chat_info}, request=request)
				return JsonResponse({'html': html,
									'url' : reverse("add_chat")
				})
		else:
			return render(request, "pong/add_chat.html", {'add_chat_info' : add_chat_info})


def get_list_of_potential_chats(user, chats) :
	list_of_chats = []
	for chat in chats :
		participants = chat.participants.all()
		is_in = False
		logger.debug("chat = %s", chat)
		for users in participants :
			if (users == user) :
				is_in = True
				break
		logger.debug("in_is = %s", is_in)
		if not is_in :
			if not chat.is_private :
				list_of_chats.append(chat)
	return (list_of_chats)


def join_chat(request) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	all_chats = Chat.objects.all()
	list_of_chats = get_list_of_potential_chats(user, all_chats)
	logger.debug("list_of_chats = %s", list_of_chats)
	if request.method == "POST" :
		chat_name = request.POST.get("chat_name")
		# all_chats = Chat.objects.all()
		error_message = None
		message = None
		chat_exist = False
		for chat in all_chats :
			logger.info("on passe bien dans la boucle des chat")
			if (chat_name == chat.name) :
				chat_exist = True
				participants = chat.participants.all()
				for users in participants :
					if (users == user) :
						error_message = "You already are in that chat"
						break
				if not error_message :
					if chat.is_private == True :
						error_message = "You cant't join that chat, it is private"
					else :
						Participant.objects.get_or_create(user=user, chat=chat)
						message = f"YOU JOINED {chat_name}"
				break
		if not chat_exist :
			logger.info("On passe la aussi")
			error_message = f"{chat_name} doesn't exist. Please try again"
		logger.debug("error_message : %s", error_message)
		logger.debug("list_of_chats : %s", list_of_chats)
		if error_message :
			context = {
				'chat_info' : {
					'value' : True,
					'error_message' : error_message,
					'list_of_chats' : list_of_chats,
				}
			}
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/join_chat_content.html", context, request=request)
				return JsonResponse({'html': html,
									'url' : reverse("join_chat")
				})
			else:
				return render(request, "pong/join_chat.html", context)
		else :
			context = {
				'chat_info' : {
					'value' : True,
					'message' : message,
					'list_of_chats' : list_of_chats,
				}
			}
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/join_chat_content.html", context, request=request)
				return JsonResponse({'html': html,
									'url' : reverse("join_chat")
				})
			else:
				return render(request, "pong/join_chat.html", context)
	else :
		context = {
			'chat_info' : {
				'value' : True,
				'list_of_chats' : list_of_chats,
			}
		}
		logger.debug("context value = %s", context['chat_info']['value'])
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/join_chat_content.html", context, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("join_chat")
			})
		else:
			return render(request, "pong/join_chat.html", context)


def render_chat(request, chat_name) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	all_chats = Chat.objects.all()
	update_message = {}
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	# for chat in all_chats :
	# 	if chat.name == chat_name :
	# 		message_chat = chat.messages.all()
	# 		update_message[chat.name] = []
	# 		for message in message_chat :
	# 			update_message[chat.name].append({
	# 				'message' : message.content,
	# 				'sender' : message.sender.pseudo,
	# 				'time' : message.timestamp.isoformat()
	# 			})
	toggle = True
	list_of_chats = []
	for chat_solo in all_chats :
		list_of_chats.append(chat_solo)
	if list_of_chats :
		for chat in reversed(list_of_chats) :
			if (chat.name == chat_name) :
				messages = chat.messages.all()
				update_message[chat.name] = []
				for message in messages :
					toggle = is_blocked(user, message.sender)
					logger.debug("toggle = %s", toggle)
					if not toggle :
						logger.info("la condition est remplie")
						update_message[chat.name].append({
							'message' : message.content,
							'sender' : message.sender.pseudo,
							'time' : message.timestamp.isoformat(),
						})

				break

			# logger.debug("message_chat = %s", message_chat)
		return JsonResponse({
			'chat_found' : True,
			'update_message' : update_message,
			'user' : user.pseudo,
		})
	return JsonResponse({
		'chat_found' : False,
	})


# def logout_view(request):
	# if request.user.is_authenticated:
	#     logout(request)
	# return redirect('login')


# def logout_view(request):
	# if request.user.is_authenticated:
	#     logout(request)

	# if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#     html = render_to_string("pong/login_content.html", {}, request=request)
	#     return JsonResponse({'html': html})``
	# else:
	#     return HttpResponseRedirect(reverse('login'))

def leave_chat(request) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("index")
			})
		else:
			return HttpResponseRedirect(reverse("index"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	logger.debug("THE USER IS = %s", user)
	all_chats = Chat.objects.all()
	list_of_chats = []
	for chat in all_chats :
		participants = chat.participants.all()
		is_in = False
		for users in participants :
			logger.debug("chats = %s", chat)
			logger.debug("user = %s", users)
			if (users.pseudo == user.pseudo) :
				is_in = True
			if is_in :
				list_of_chats.append(chat)
				break
	logger.debug("list_of_chats = %s", list_of_chats)
	context = {
		'error_message' : None,
		'message' : None,
		'list_of_chats' : []
	}
	if list_of_chats :
		context['list_of_chats'] = list_of_chats
	if request.method == "POST" :
		chat_exist = False
		chat_name = request.POST.get("chat_name")
		for chat in all_chats :
			if chat.name == chat_name :
				chat_exist = True
				break
		if chat_exist :
			user_in_chat = False
			for chats in list_of_chats :
				if chats.name == chat_name :
					user_in_chat = True
					break
			# if user_in_chat :
			# 	participant_pool = chats.participants.all()
			# 	for participant in participant_pool :
			# 		if participant.pseudo == user.pseudo :
			# 			participant.delete()
			# 			message = f"You leaved {chat_name}"
			# 			context['message'] = message
			# 	participant_pool = chats.participants.all()
			# 	if not participant_pool :
			# 		chats.delete()
			if user_in_chat:
				participant_pool = chats.participants.all()
				participant_to_remove = None
				for participant in participant_pool:
					if participant.pseudo == user.pseudo:
						participant_to_remove = participant
						break
				if participant_to_remove:
					chats.participants.remove(participant_to_remove)
					message = f"You leaved {chats.name}"
					context['message'] = message
				participant_pool = chats.participants.all()
				if not participant_pool:
					chats.delete()
				else :
					chats.save()
			else :
				error_message = f"You are not in that chat"
				context['error_message'] = error_message
		else :
			error_message = f"{chat_name} doesn't exist"
			context['error_message'] = error_message
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/leave_chat_content.html", context, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("leave_chat")
			})
	else:
		return render(request, "pong/leave_chat.html", context)



###PROFILE###
def logout_view(request):
	if request.user.is_authenticated:
		user = NewUser.objects.get(id=(request.session.get('user_id')))
		user.is_active_status = False
		user.save()
		logout(request)
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/login_content.html", {}, request=request)
		return JsonResponse({'html': html,
								'url' : reverse('login')})
	else:
		return HttpResponseRedirect(reverse('login'))

def check_box(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html,
								'url' : reverse("login")
								})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	if request.method == "POST":
		if request.POST.get("options"):
			logger.info("->>>>>>>>>>>>>>>>>>>>>>")
			choice = request.POST.get("options")
			if choice == "y":
				logger.info("y")
				user.is_mfa_enabled = True
				user.save()
			else:
				logger.info("n")
				user.is_mfa_enabled = False
				user.save()
	return JsonResponse({
		'mfa': user.is_mfa_enabled
	})

def profile_view(request):
	#gérer block user
	#gérer cliquer sur un user et redirigé vers profil plus simple
	#faire spa
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html,
								'url' : reverse("login")
								})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = NewUser.objects.get(id=(request.session.get('user_id')))
	url = pyotp.totp.TOTP(user.mfa_hash).provisioning_uri(name=user.email, issuer_name="Pong")
	qr = qrcode.make(url)
	buffered = BytesIO()
	qr.save(buffered)
	qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
	try:
		user_avatar = user.avatar.url
	except ValueError:
		user_avatar = None
	friends = get_friends(user)
	password_form_errors = []
	other_error  = {
		"avatar" : None,
		"email" : None,
		"pseudo" : None
	}

	logger.debug("friend = %s", friends)
	if request.method == "POST":
		# if request.POST.get("options"):
		# 	choice = request.POST.get("options")
		# 	if choice == "enabled":
		# 		user.is_mfa_enabled = True
		# 		user.save()
		# 	else:
		# 		user.is_mfa_enabled = False
		# 		user.save()
		# 	return HttpResponseRedirect(reverse("profile"))
		if request.POST.get("change_pseudo"):
			if user.pseudo is not request.POST.get("change_pseudo"):
				try:
					test = NewUser.objects.get(pseudo=request.POST.get("change_pseudo"))
					other_error["pseudo"] = "this pseudo already exist"
				except NewUser.DoesNotExist:
					user.pseudo = request.POST.get("change_pseudo")
					user.save()
			else:
				other_error["pseudo"] = "you are already name like this"

		if request.FILES.get("change_avatar"):
			user.avatar = request.FILES.get("change_avatar")
			user.save()
			user_avatar = user.avatar.url
			update_session_auth_hash(request, user)
		if request.POST.get("change_email"):
			if user.email is not request.POST.get("change_email"):
				try:
					test = NewUser.objects.get(email=request.POST.get("change_email"))
					other_error["email"] =  "this email already exist"
				except NewUser.DoesNotExist:
					user.email = request.POST.get("change_email")
					user.save()
					update_session_auth_hash(request, user)
			else:
				other_error["email"] = "your email is already this one"

		if request.POST.get("old_password"):
			old_password = request.POST.get("old_password")
			new_password1 = request.POST.get("new_password1")
			new_password2 = request.POST.get("new_password2")

			if new_password1 and new_password2 and old_password:
				if new_password1 == new_password2:
					if user.check_password(old_password):
						user.set_password(new_password1)
						user.save()
						update_session_auth_hash(request, user)  # Important to update session
						return HttpResponseRedirect(reverse("index"))
					else:
						password_form_errors.append('Old password is incorrect.')
				else:
					password_form_errors.append('New passwords do not match.')
			else:
				password_form_errors.append('Please fill out all password fields.')

	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/profile_content.html", {
														'user_info' : {
															'user_choice' : user.is_mfa_enabled,
															'user_url'    : qr_base64,
															'user_pseudo' : user.pseudo,
															'user_email' : user.email,
															'user_avatar' : user_avatar,
															'user_friends' : friends,
															'user_blocked_users': "test"

															},
															'password_form_errors': password_form_errors,
															'other_error': other_error}, request=request)
		return JsonResponse({'html': html,
								'url' : reverse("profile")
								})
	else:
		return render(request, "pong/profile.html", {
														'user_info' : {
															'user_choice' : user.is_mfa_enabled,
															'user_url'    : qr_base64,
															'user_pseudo' : user.pseudo,
															'user_email' : user.email,
															'user_avatar' : user_avatar,
															'user_friends' : friends,
															'user_blocked_users': "test"

															},
															'password_form_errors': password_form_errors,
															'other_error': other_error
													})


def recup_user_info(user) :
	url = pyotp.totp.TOTP(user.mfa_hash).provisioning_uri(name=user.email, issuer_name="Pong")
	qr = qrcode.make(url)
	buffered = BytesIO()
	qr.save(buffered)
	qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
	try:
		user_avatar = user.avatar.url
	except ValueError:
		user_avatar = None
	friends = get_friends(user)
	other_error  = {
		"avatar" : None,
		"email" : None,
		"pseudo" : None
	}
	user_info = {
					'user_info' : {
						'user_choice' : user.is_mfa_enabled,
						'user_url' : qr_base64,
						'user_pseudo' : user.pseudo,
						'user_avatar' : user_avatar,
						'user_friends' : friends,
					}, 'other_error': other_error
	}
	return user_info



# def add_friends(request):
	# if not request.user.is_authenticated:
	#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#         html = render_to_string("pong/login_content.html", {}, request=request)
	#         return JsonResponse({'html': html})
	#     else:
	#         return HttpResponseRedirect(reverse("login"))

	# user = NewUser.objects.get(id=(request.session.get('user_id')))

	# if request.method == "POST":
	#     friend_pseudo = request.POST.get("friend_pseudo")
	#     friend_user = None
	#     try:
	#         friend_user = NewUser.objects.get(pseudo=friend_pseudo)
	#     except NewUser.DoesNotExist:
	#         friend_user = None
	#     #empecher d'etre amis avec sois même
	#     if ( friend_user is not None) and (user.id is not friend_user.id) :
	#         # Check if they are already friends
	#         if Friendship.objects.filter(person1=user, person2=friend_user).exists() or Friendship.objects.filter(person1=friend_user, person2=user).exists():
	#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#                 html = render_to_string("pong/add_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : "you are already friends"
	#                                                             }
	#                                         }, request=request)
	#                 return JsonResponse({'html': html,
	#                             'url' : reverse("add_friends")
	#                 })
	#             else:
	#                 return render(request, "pong/add_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : "you are already friends"
	#                                                             }
	#                                         })

	#     # Create the friendship
	#         Friendship.objects.create(person1=user, person2=friend_user)
	#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#             html = render_to_string("pong/add_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : "you are now friends"
	#                                                             }
	#                                         }, request=request)
	#             return JsonResponse({'html': html,
	#                             'url' : reverse("add_friends")
	#                 })
	#         else:
	#             return render(request, "pong/add_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : "you are now friends"
	#                                                             }
	#                                         })

	#     else:
	#         if friend_user is None:
	#             message = "this user doesn't exist"
	#         else:
	#             message = "you can't add yourself as friend"
	#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#                 html = render_to_string("pong/add_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                         }, request=request)
	#                 return JsonResponse({'html': html,
	#                             'url' : reverse("add_friends")
	#                 })
	#         else:
	#             return render(request, "pong/add_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                         })
	# else:
	#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#                 html = render_to_string("pong/add_friends_content.html", {'error_message' : {
	#                                                                     'value' : False,
	#                                                                     'message' : "nothing"
	#                                                             }
	#                                         }, request=request)
	#                 return JsonResponse({'html': html,
	#                             'url' : reverse("add_friends")
	#                 })
	#     else:
	#         return render(request, "pong/add_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : False,
	#                                                                     'message' : "nothing"
	#                                                             }
	#                                         })


def add_friends(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html})
		else:
			return HttpResponseRedirect(reverse("login"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	friend_user = get_friends(user)
	logger.debug("la liste des users amis : %s", friend_user)
	all_users = NewUser.objects.all()
	logger.debug("la liste des users  : %s", all_users)
	users_list = []
	for users in all_users :
		# logger.debug("amis = %s", users)
		if users not in friend_user and users != user and users.pseudo != "admin":
			users_list.append(users)
	logger.debug("la liste des users non amis : %s", users_list)
	if request.method == "POST":
		friend_pseudo = request.POST.get("friend_pseudo")
		friend_user = None
		try:
			friend_user = NewUser.objects.get(pseudo=friend_pseudo)
		except NewUser.DoesNotExist:
			friend_user = None
		#empecher d'etre amis avec sois même
		if ( friend_user is not None) and (user.id is not friend_user.id) :
			# Check if they are already friends
			if Friendship.objects.filter(person1=user, person2=friend_user).exists() or Friendship.objects.filter(person1=friend_user, person2=user).exists():
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : "you are already friends"
																}, 'users_list' : users_list,
											}, request=request)
					return JsonResponse({'html': html,
								'url' : reverse("add_friends")
					})
				else:
					return render(request, "pong/add_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : "you are already friends"
																}, 'users_list' : users_list,
											})

		# Create the friendship
			Friendship.objects.create(person1=user, person2=friend_user)
			logger.debug("friend_user = %s", friend_user)
			temp = friend_user.pseudo.upper()
			logger.debug("friend_user apres = %s", friend_user)
			message = temp + " IS NOW YOUR FRIEND"
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/add_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'users_list' : users_list,
											}, request=request)
				return JsonResponse({'html': html,
								'url' : reverse("add_friends")
					})
			else:
				return render(request, "pong/add_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'users_list' : users_list,
											})

		else:
			if friend_user is None:
				message = "this user doesn't exist"
			else:
				message = "you can't add yourself as friend"
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'users_list' : users_list,
											}, request=request)
					return JsonResponse({'html': html,
								'url' : reverse("add_friends")
					})
			else:
				return render(request, "pong/add_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'users_list' : users_list,
											})
	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/add_friends_content.html", {'error_message' : {
																		'value' : False,
																		'message' : "nothing"
																}, 'users_list' : users_list,
											}, request=request)
					return JsonResponse({'html': html,
								'url' : reverse("add_friends")
					})
		else:
			return render(request, "pong/add_friends.html", {
												'error_message' : {
																		'value' : False,
																		'message' : "nothing"
																}, 'users_list' : users_list,
											})




# def delete_friends(request):
	# if not request.user.is_authenticated:
	#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#         html = render_to_string("pong/login_content.html", {}, request=request)
	#         return JsonResponse({'html': html})
	#     else:
	#         return HttpResponseRedirect(reverse("login"))

	# user = NewUser.objects.get(id=(request.session.get('user_id')))

	# if request.method == "POST":
	#     friend_pseudo = request.POST.get("friend_pseudo")
	#     friend_user = None
	#     try:
	#         friend_user = NewUser.objects.get(pseudo=friend_pseudo)
	#     except NewUser.DoesNotExist:
	#         friend_user = None

	#     if ( friend_user is not None) and (user.id is not friend_user.id) :
	#         friendship = Friendship.objects.filter(Q(person1=user, person2=friend_user) | Q(person1=friend_user, person2=user)).first()
	#         if friendship:
	#             friendship.delete()
	#         else:
	#             message = "you are not friends"
	#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#                 html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                         }, request=request)
	#                 return JsonResponse({'html': html,
	#                             'url' : reverse("delete_friends")
	#                 })
	#             return render(request, "pong/delete_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                             })


	#         #succes delete friend
	#         message = "you are not friends anymore"
	#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#             html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                         }, request=request)
	#             return JsonResponse({'html': html,
	#                             'url' : reverse("delete_friends")
	#                 })
	#         else:
	#             return render(request, "pong/delete_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                             })
	#     else:
	#         if friend_user is None:
	#             message = "this user doesn't exist"
	#         else:
	#             message = "you can't delete yourself as friend"

	#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#             html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                         }, request=request)
	#             return JsonResponse({'html': html,
	#                             'url' : reverse("delete_friends")
	#                 })
	#         else:
	#             return render(request, "pong/delete_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : True,
	#                                                                     'message' : message
	#                                                             }
	#                                             })
	# else:
	#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
	#         html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
	#                                                                     'value' : False,
	#                                                                     'message' : "nothing"
	#                                                             }
	#                                         }, request=request)
	#         return JsonResponse({'html': html,
	#                             'url' : reverse("delete_friends")
	#                 })
	#     else:
	#             return render(request, "pong/delete_friends.html", {
	#                                             'error_message' : {
	#                                                                     'value' : False,
	#                                                                     'message' : "nothing"
	#                                                             }
	#                                                             }
	#                                                             )


def delete_friends(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = NewUser.objects.get(id=(request.session.get('user_id')))

	user_friend = get_friends(user)

	if request.method == "POST":
		friend_pseudo = request.POST.get("friend_pseudo")
		friend_user = None
		try:
			friend_user = NewUser.objects.get(pseudo=friend_pseudo)
		except NewUser.DoesNotExist:
			friend_user = None

		if ( friend_user is not None) and (user.id is not friend_user.id) :
			friendship = Friendship.objects.filter(Q(person1=user, person2=friend_user) | Q(person1=friend_user, person2=user)).first()
			if friendship:
				friendship.delete()
			else:
				message = "you are not friends"
				if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
					html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
											}, request=request)
					return JsonResponse({'html': html,
								'url' : reverse("delete_friends")
					})
				return render(request, "pong/delete_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
												})


			#succes delete friend
			message = "you are not friends anymore"
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
											}, request=request)
				return JsonResponse({'html': html,
								'url' : reverse("delete_friends")
					})
			else:
				return render(request, "pong/delete_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
												})
		else:
			if friend_user is None:
				message = "this user doesn't exist"
			else:
				message = "you can't delete yourself as friend"

			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
											}, request=request)
				return JsonResponse({'html': html,
								'url' : reverse("delete_friends")
					})
			else:
				return render(request, "pong/delete_friends.html", {
												'error_message' : {
																		'value' : True,
																		'message' : message
																}, 'user_friend' : user_friend,
												})
	else:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/delete_friends_content.html", {'error_message' : {
																		'value' : False,
																		'message' : "nothing"
																}, 'user_friend' : user_friend,
											}, request=request)
			return JsonResponse({'html': html,
								'url' : reverse("delete_friends")
					})
		else:
				return render(request, "pong/delete_friends.html", {
												'error_message' : {
																		'value' : False,
																		'message' : "nothing"
																}, 'user_friend' : user_friend,
																})



def other_profile(request, username) :
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request=request)
			return JsonResponse({'html': html})
		else:
			return HttpResponseRedirect(reverse("login"))
	user = NewUser.objects.get(id=(request.session.get('user_id')))
	# logger.debug("user = %s", user)
	# logger.info("Je passe la dans other profile")
	# username = username
	# logger.debug("username = %s", username)
	context = {
		'user_target' :{
						'token' : False
		}
	}
	# data = update_stats(user) ici seront les infos de l'user : email etc
	# logger.debug("context = %s", context)
	# logger.debug("context=%s", data)
	all_users = NewUser.objects.all()
	user_target = None
	is_friend = False
	# logger.debug("all Users = %s", all_users)
	for user_found in all_users :
		if user_found.pseudo == username :
			user_target = user_found
			break
	if user_target.pseudo == user.pseudo :
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/profile_content.html", context, request=request)
			return JsonResponse({'html': html,
								'url' : ("profile")})
		else:
			return render(request, "pong/profile.html", context)
	# logger.debug("user_target email = %s", user_target.email)
	# logger.debug("user_target pseudo = %s", user_target.pseudo)
	# logger.debug("user_target password = %s", user_target.password)
	# logger.debug("user_target avatar = %s", user_target.avatar)
	# logger.debug("user_target stats = %s", user_target.statistic)
	# logger.debug("user_target = %s", user_target)
	data_pong = {}
	data_tic = {}
	user_friend = get_friends(user)
	try:
		user_target_avatar = user_target.avatar.url
	except ValueError:
		user_target_avatar = None
	# logger.debug("friends = %s", user_friend)
	for friend in user_friend :
		if friend.pseudo == user_target.pseudo :
			is_friend = True
			break
	# logger.debug("user_target.statistic = %s", user_target.statistic)
	# if Party.objects.exists() :
	pong_partys = Party.objects.filter(game_name="pong")
	if (pong_partys.exists()) :
		data_pong = update_stats_other_profile(user_target, pong_partys, "pong")
	tic_partys = Party.objects.filter(game_name="tic")
	if (tic_partys.exists()) :
		data_tic = update_stats_other_profile(user_target, tic_partys, "tic")
	# logger.debug("data_pong other user = %s", data_pong)
	# logger.debug("data_tic other user = %s", data_tic)
	# history = []
	# partie = Party.objects.all()
	# for game in partie :
	# 	winner = game.winner.pseudo.strip()
	# 	loser = game.loser.pseudo.strip()
	# 	if ((user.pseudo == winner) or (user.pseudo == loser)) :
	# 		history.append(game)
	logger.debug("data_pong = %s", data_pong)
	logger.debug("data_tic = %s", data_tic)
	context = {
		'user_target' : {
						'token' : True,
						'username' : user_target.pseudo,
						'is_friend' : is_friend,
						'user_avatar' : user_target_avatar,
						'pong_stats' : data_pong,
						'tic_stats' : data_tic,
		}
	}
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/other_profile_content.html", context, request=request)
			return JsonResponse({'html': html,
								'url' : (f"/other_profile/{username}")})
	else:
		return render(request, "pong/other_profile.html", context)


###################### HOME GAME
def home_game(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/home_game_content.html", {}, request=request)
		return JsonResponse({'html': html, 'url' : reverse("home_game") })
	else:
		return render(request, "pong/home_game.html", {})

###################### PONG
def waiting_pong(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	other_user = NewUser.objects.filter(in_waiting_pong=True).exclude(id=user.id).first()
	if other_user:
		party = Party.objects.create(winner=user, loser=other_user, user_red=user, user_blue=other_user, game_name='pong', game_time=timedelta(minutes=0))
		user.in_waiting_pong = False
		other_user.in_waiting_pong = False
		user.save()
		other_user.save()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/waiting_pong_content.html", {}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("waiting_pong") })
		else:
			return render(request, "pong/waiting_pong.html", {})
	else:
		user.in_waiting_pong = True
		user.save()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/waiting_pong_content.html", {}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("waiting_pong") })
		else:
			return render(request, "pong/waiting_pong.html", {})

def check_pong_match(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	party = Party.objects.filter(Q(user_red=user) | Q(user_blue=user), is_ended=False).last()
	if party and party.user_red and party.user_blue:
		print(" ")
		print("found OK !")
		print(" ")
		party.user_red.in_waiting_pong = False
		party.user_blue.in_waiting_pong = False
		party.user_red.save()
		party.user_blue.save()
		if party.user_red == user:
			return JsonResponse({
				'match_found': True,
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
				'other_client': False
			})
		else:
			return JsonResponse({
				'match_found': False,
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
				'other_client': True
			})

	else:
		print(" ")
		print("Nothing")
		print(" ")
		return JsonResponse({'match_found': False})

def pong_page(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	party = get_object_or_404(Party, id=party_id)
	if party.is_ended:
		return HttpResponseRedirect(reverse("home_game"))

	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		if party.tournament:
			html = render_to_string("pong/pong_page_content.html", {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'alias_red': party.tournament.alias1,
				'alias_blue': party.tournament.alias2,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("pong_page", args=[party_id]) })
		else:
			html = render_to_string("pong/pong_page_content.html", {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("pong_page", args=[party_id]) })
	else:
		if party.tournament:
			return render(request, 'pong/pong_page.html', {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'alias_red': party.tournament.alias1,
				'alias_blue': party.tournament.alias2,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			})
		else:
			return render(request, 'pong/pong_page.html', {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			})

def scoring_pong(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	party = get_object_or_404(Party, id=party_id)
	if not party.is_ended:
		if (request.POST.get("red_score") > request.POST.get("blue_score")):
			party.winner = party.user_red
			party.loser = party.user_blue
		else:
			party.winner = party.user_blue
			party.loser = party.user_red
		party.winner.in_waiting_pong = False
		party.loser.in_waiting_pong = False
		party.score_red = request.POST.get("red_score")
		party.score_blue = request.POST.get("blue_score")
		party.game_time = timedelta(milliseconds=int(request.POST.get("game_time")))
		party.is_ended = True
		party.save()
	return JsonResponse({
		'end_correctly': True,
	})

def check_pong_status(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	try:
		party = Party.objects.get(id=party_id)
		return JsonResponse({
			'party': True,
			'is_ended': party.is_ended,
			'id_party': party.id,
		})
	except ObjectDoesNotExist:
		return JsonResponse({
			'party': False,
			'is_ended': False,
			'id_party': False,
		})

def stop_waiting_pong(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	request.user.in_waiting_pong = False
	request.user.save()
	return JsonResponse({'everything_good': True})


###################### TOURNAMENT
def tournament(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	if request.method == 'POST':
		alias = request.POST.get("alias")
		if not alias:
			return JsonResponse({
				'message': "the input alias cannot be empty",
			})


	# 1st IF
	tournament = Tournament.objects.filter(
		Q(participant1=request.user) |
		Q(participant2=request.user) |
		Q(participant3=request.user) |
		Q(participant4=request.user),
		winner__isnull=True
	).last()

	if tournament:
		if not tournament.participant1 or not tournament.participant2 or not tournament.participant3 or not tournament.participant4:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/tournament_content.html", {}, request=request)
				return JsonResponse({'html': html, 'url' : reverse("tournament") })
			else:
				return render(request, "pong/tournament.html", {'message': 'Waiting for more players.'})

	# ELSE IF du cahier
	tournament = Tournament.objects.filter(
		~Q(participant1=request.user),
		~Q(participant2=request.user),
		~Q(participant3=request.user),
		~Q(participant4=request.user),
		winner__isnull=True
	).filter(
		Q(participant2__isnull=True) |
		Q(participant3__isnull=True) |
		Q(participant4__isnull=True)
	).last()


	if tournament:
		logger.debug("tournament.participant1 %s: ", tournament.participant1)
		logger.debug("tournament.participant2 %s: ", tournament.participant2)
		logger.debug("tournament.participant3 %s: ", tournament.participant3)
		logger.debug("tournament.participant4 %s: ", tournament.participant4)
		logger.info("---------------")
		if not tournament.participant2:
			if tournament.alias1 == alias:
				return JsonResponse({
					'message': "this alias is already taken",
				})
			tournament.participant2 = request.user
			tournament.alias2 = alias
		elif not tournament.participant3:
			if tournament.alias1 == alias or tournament.alias2 == alias:
				return JsonResponse({
					'message': "this alias is already taken",
				})
			tournament.participant3 = request.user
			tournament.alias3 = alias
		elif not tournament.participant4:
			if tournament.alias1 == alias or tournament.alias2 == alias or tournament.alias3 == alias:
				return JsonResponse({
					'message': "this alias is already taken",
				})
			tournament.participant4 = request.user
			tournament.alias4 = alias
		tournament.save()

		if tournament.participant1 and tournament.participant2 and tournament.participant3 and tournament.participant4:
			if not tournament.party1:
				tournament.party1 = Party.objects.create(
					game_name="pong",
					winner=tournament.participant1,
					loser=tournament.participant2,
					user_red=tournament.participant1,
					user_blue=tournament.participant2,
					game_time=timedelta(minutes=0),
					tournament=tournament)
				tournament.save()
			return redirect('pong_page', party_id=tournament.party1.id)
		else:
			if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
				html = render_to_string("pong/tournament_content.html", {}, request=request)
				return JsonResponse({'html': html, 'url' : reverse("tournament") })
			else:
				return render(request, "pong/tournament.html", {'message': 'You have joined an existing tournament.'})

	# GROS ELSE build
	Tournament.objects.create(participant1=request.user, alias1=alias)
	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/tournament_content.html", {}, request=request)
		return JsonResponse({'html': html, 'url' : reverse("tournament") })
	else:
		return render(request, "pong/tournament.html", {'message': 'You have created a new tournament.'})

def check_tournament_match(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	tournament = Tournament.objects.filter(
		Q(participant1=request.user) |
		Q(participant2=request.user) |
		Q(participant3=request.user) |
		Q(participant4=request.user)
	).last()

	if tournament:
		if tournament.participant1 and tournament.participant2 and tournament.participant3 and tournament.participant4:
			return JsonResponse({
				'tournament_found': True,
			})
		else:
			return JsonResponse({
				'tournament_found': False,
			})
	else:
		return JsonResponse({
			'tournament_found': False,
		})

def scoring_tournament(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	party = get_object_or_404(Party, id=party_id)
	if (request.POST.get("red_score") > request.POST.get("blue_score")):
		party.winner = party.user_red
		party.loser = party.user_blue
	else:
		party.winner = party.user_blue
		party.loser = party.user_red
	party.winner.in_waiting_pong = False
	party.loser.in_waiting_pong = False
	party.score_blue = request.POST.get("blue_score")
	party.score_red = request.POST.get("red_score")
	party.is_ended = True
	party.save()

	participant1 = party.tournament.participant1
	participant2 = party.tournament.participant2
	participant3 = party.tournament.participant3
	participant4 = party.tournament.participant4

	if not party.tournament.party2:
		logger.info("party2")
		party.tournament.party2 = Party.objects.create(
			winner=participant3,
			loser=participant4,
			user_red=participant3,
			user_blue=participant4,
			game_name='pong',
			game_time=timedelta(minutes=0),
			tournament=party.tournament)
		party.tournament.save()
		party.save()
		logger.debug("ared: %s", party.tournament.alias3)
		logger.debug("ablue: %s", party.tournament.alias4)

		return JsonResponse({
			'end_correctly': True,
			'party_id': party.tournament.party2.id,
			'user_red': participant3.pseudo,
			'user_blue': participant4.pseudo,
			'alias_red': party.tournament.alias3,
			'alias_blue': party.tournament.alias4,
		})
	elif not party.tournament.party3:
		logger.debug("W1: %s", party.tournament.party1.winner.pseudo)
		logger.debug("W2: %s", party.tournament.party2.winner.pseudo)
		party.tournament.party3 = Party.objects.create(
			winner=party.tournament.party1.winner,
			loser=party.tournament.party2.winner,
			user_red=party.tournament.party1.winner,
			user_blue=party.tournament.party2.winner,
			game_name='pong',
			game_time=timedelta(minutes=0),
			tournament=party.tournament)
		party.tournament.save()
		party.save()
		alias_red = None
		alias_blue = None

		if party.tournament.party1.winner.pseudo == party.tournament.participant1.pseudo:
			alias_red = party.tournament.alias1
		elif party.tournament.party1.winner.pseudo == party.tournament.participant2.pseudo:
			alias_red = party.tournament.alias2
		elif party.tournament.party1.winner.pseudo == party.tournament.participant3.pseudo:
			alias_red = party.tournament.alias3
		elif party.tournament.party1.winner.pseudo == party.tournament.participant4.pseudo:
			alias_red = party.tournament.alias4

		if party.tournament.party2.winner.pseudo == party.tournament.participant1.pseudo:
			alias_blue = party.tournament.alias1
		elif party.tournament.party2.winner.pseudo == party.tournament.participant2.pseudo:
			alias_blue = party.tournament.alias2
		elif party.tournament.party2.winner.pseudo == party.tournament.participant3.pseudo:
			alias_blue = party.tournament.alias3
		elif party.tournament.party2.winner.pseudo == party.tournament.participant4.pseudo:
			alias_blue = party.tournament.alias4
		logger.debug("ared: %s", alias_red)
		logger.debug("ablue: %s", alias_blue)
		return JsonResponse({
			'end_correctly': True,
			'party_id': party.tournament.party3.id,
			'user_red': party.tournament.party1.winner.pseudo,
			'user_blue': party.tournament.party2.winner.pseudo,
			'alias_red': alias_red,
			'alias_blue': alias_blue,
		})
	elif party.tournament.party3:
		logger.info("-- -fin- --")
		party.tournament.winner = party.tournament.party3.winner
		party.tournament.save()
		party.save()

	party.save()
	return JsonResponse({
		'end_correctly': False,
		'party_id': party.id
	})


###################### TIC TAC TOE
def waiting_tic(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	other_user = NewUser.objects.filter(in_waiting_tic=True).exclude(id=user.id).first()
	if other_user:
		party = Party.objects.create(winner=user, loser=other_user, user_red=user, user_blue=other_user, game_name='tic', game_time=timedelta(minutes=0))
		user.in_waiting_tic = False
		other_user.in_waiting_tic = False
		user.save()
		other_user.save()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/waiting_tic_content.html", {}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("waiting_tic") })
		else:
			return render(request, "pong/waiting_tic.html", {})
	else:
		user.in_waiting_tic = True
		user.save()
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/waiting_tic_content.html", {}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("waiting_tic") })
		else:
			return render(request, "pong/waiting_tic.html", {})

def check_tic_match(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	user = request.user
	party = Party.objects.filter(Q(user_red=user) | Q(user_blue=user), is_ended=False).last()
	if party and party.user_red and party.user_blue:
		print(" ")
		print("found OK !")
		print(" ")
		# party.user_red.in_waiting_tic = False
		# party.user_blue.in_waiting_tic = False
		# party.user_red.save()
		# party.user_blue.save()
		if party.user_red == user:
			return JsonResponse({
				'match_found': True,
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
				'other_client': False
			})
		else:
			return JsonResponse({
				'match_found': False,
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
				'other_client': True
			})

	else:
		print(" ")
		print("Nothing")
		print(" ")
		return JsonResponse({'match_found': False})

def tic(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	party = get_object_or_404(Party, id=party_id)
	if party.is_ended:
		return HttpResponseRedirect(reverse("home_game"))

	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		if party.tournament:
			html = render_to_string("pong/tic_content.html", {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'alias_red': party.tournament.alias1,
				'alias_blue': party.tournament.alias2,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("tic", args=[party_id]) })
		else:
			html = render_to_string("pong/tic_content.html", {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			}, request=request)
			return JsonResponse({'html': html, 'url' : reverse("tic", args=[party_id]) })
	else:
		if party.tournament:
			return render(request, 'pong/tic.html', {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'alias_red': party.tournament.alias1,
				'alias_blue': party.tournament.alias2,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			})
		else:
			return render(request, 'pong/tic.html', {
				'party_end': party.is_ended,
				'party_id': party.id,
				'user_red': party.user_red.pseudo,
				'user_blue': party.user_blue.pseudo,
				'id_red': party.user_red.id,
				'id_blue': party.user_blue.id,
			})

def scoring_tic(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	party = get_object_or_404(Party, id=party_id)
	if not party.is_ended:
		if (request.POST.get("red_score") > request.POST.get("blue_score")):
			party.winner = party.user_red
			party.loser = party.user_blue
		else:
			party.winner = party.user_blue
			party.loser = party.user_red
		party.winner.in_waiting_tic = False
		party.loser.in_waiting_tic = False
		party.score_red = request.POST.get("red_score")
		party.score_blue = request.POST.get("blue_score")
		party.game_time = timedelta(milliseconds=int(request.POST.get("game_time")))
		party.is_ended = True
		party.save()
	return JsonResponse({
		'end_correctly': True,
	})

def check_tic_status(request, party_id):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	try:
		party = Party.objects.get(id=party_id)
		return JsonResponse({
			'party': True,
			'is_ended': party.is_ended,
			'id_party': party.id,
		})
	except ObjectDoesNotExist:
		return JsonResponse({
			'party': False,
			'is_ended': False,
			'id_party': False,
		})

def stop_waiting_tic(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	request.user.in_waiting_tic = False
	request.user.save()
	return JsonResponse({'everything_good': True})



# user_id = request.session.get('user_id')
# 	if not user_id:
# 		return HttpResponseRedirect(reverse("index"))

# 	user = get_object_or_404(NewUser.objects.select_related('statistic'), id=user_id)

# 	# Déboguer la valeur de user.statistic
# 	logger.debug("User: %s", user)
# 	logger.debug("User.statistic: %s", user.statistic)

# 	# Vérifier si user.statistic est nul ou non
# 	if user.statistic is None:
# 		logger.info("On passe la")
# 		user_statistic, created = Statistic.objects.get_or_create(user=user)
# 		user_statistic.save()
# 	else:
# 		logger.info("Statistique déjà existante")



def pong_ai(request):
	if not request.user.is_authenticated:
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			html = render_to_string("pong/login_content.html", {}, request)
			return JsonResponse({'html': html, 'url' : reverse("login")})
		else:
			return HttpResponseRedirect(reverse("login"))

	if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
		html = render_to_string("pong/pong_ai_content.html", {
				'user': request.user.pseudo,
			}, request=request)
		return JsonResponse({'html': html, 'url' : reverse("pong_ai") })
	else:
		return render(request, "pong/pong_ai.html", {'user': request.user.pseudo})
