from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from base64 import b64encode
from django.core.files.base import ContentFile
from .utils import get_friends #, CustomPasswordChangeForm
from .models import NewUser, Tournament, Party, Chat, Message, Statistic, Participant, Friendship, BlockedUser
from datetime import datetime
from django.db.models import Q
from django.db import IntegrityError
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
        try :
            index = email.index("@")
        except ValueError :
            logger.info("On passe ici exception")
            return ('')
        for i in range(len(email)):
            if email[i] == '@':
                if i + 1 < len(email) and not email[i + 1].isalnum():
                    return ''
            if email[i] == ' ':
                return ''
        if not (email.endswith("com") or email.endswith(".fr")) :
            return ('')
    
        # Test de la fonction
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

        test_mail()

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
        user.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string("pong/homepage_content.html", {}, request=request)
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
    user = authenticate(request, email=email, password=password)
    print("email =", email, "password =", password)
    if user is not None:
        request.session['user_id'] = user.id
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
        return {'error_message': "Invalid credentials."}

def signin(request):
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
        print("Je passe ici quand j'appuie sur LOGIN oui")
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        result = handle_authentication(request, email, password)
        
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
            return JsonResponse({'html': html,
                                'url' : reverse("index")
            })
        else:
            value = True
            message = 'invalid one time password or the password has expired'
            html = render_to_string("pong/otp_content.html", {'error_message': {
                    'value': value,
                    'message': message
                }}, request=request)
            return JsonResponse({'html': html,
                                'url' : reverse('otp')
            })

    return render(request, "pong/otp.html")

def statistics(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))
    user = NewUser.objects.get(id=(request.session.get('user_id')))
    statistics = user.statistic
    history = []
    partie = Party.objects.all()
    for game in partie :
        winner = game.winner.pseudo.strip()
        loser = game.loser.pseudo.strip()
        if ((user.pseudo == winner) or (user.pseudo == loser)) :
            history.append(game)
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
    nbr_day = 1
    for i in range(1, len(game_date)):
        if game_date[i] != game_date[i - 1]:
            nbr_day += 1
    data = {}
    game_duration = timedelta()
    for i in range(len(history)):
        game_duration += history[i].game_time
        if ((i == len(history) - 1) or (history[i].date.strftime('%Y-%m-%d') != history[i + 1].date.strftime('%Y-%m-%d'))) :
            data[history[i].date.strftime('%Y-%m-%d')] = game_duration.total_seconds()
            game_duration = timedelta()
    return render(request, "pong/statistics.html", {
                                                    'user' : user,
                                                    'statistics' : statistics,
                                                    'history' : history,
                                                    'game_dates_json': json.dumps(game_date),
                                                    'game_results_json': json.dumps(game_result_numeric),
                                                    'game_duration_json' : json.dumps(data)
                                                    })

def chat(request):
    return render(request, "pong/chat.html")

# def logout_view(request):
    # if request.user.is_authenticated:
    #     logout(request)
    # return redirect('login')


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string("pong/login_content.html", {}, request=request)
        return JsonResponse({'html': html})
    else:
        return HttpResponseRedirect(reverse('login'))


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

    
    if request.method == "POST":
        if request.POST.get("options"):
            choice = request.POST.get("options")
            if choice == "enabled":
                user.is_mfa_enabled = True
                user.save()
            else:
                user.is_mfa_enabled = False
                user.save()
            #return HttpResponseRedirect(reverse("profile"))
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



def add_friends(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    user = NewUser.objects.get(id=(request.session.get('user_id')))
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
                return render(request, "pong/add_friends.html", {
                                                'error_message' : {
                                                                        'value' : True,
                                                                        'message' : "you are already friends"
                                                                }
                                            })

        # Create the friendship
            Friendship.objects.create(person1=user, person2=friend_user)
            return HttpResponseRedirect(reverse("profile"))
        else:
            if friend_user is None:
                message = "this user doesn't exist"
            else:
                message = "you can't add yourself as friend"
            return render(request, "pong/add_friends.html", {
                                                'error_message' : {
                                                                        'value' : True,
                                                                        'message' : message
                                                                }
                                            })
    else:
        return render(request, "pong/add_friends.html", {
                                                'error_message' : {
                                                                        'value' : False,
                                                                        'message' : "nothing"
                                                                }
                                            })




def delete_friends(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    user = NewUser.objects.get(id=(request.session.get('user_id')))
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
                return render(request, "pong/delete_friends.html", {
                                                'error_message' : {
                                                                        'value' : True,
                                                                        'message' : message
                                                                }
                                                })       
            return HttpResponseRedirect(reverse("profile")) #succes delete frfiend 
        else:
            if friend_user is None:
                message = "this user doesn't exist"
            else:
                message = "you can't delete yourself as friend"
            return render(request, "pong/delete_friends.html", {
                                                'error_message' : {
                                                                        'value' : True,
                                                                        'message' : message
                                                                }
                                            })
    else:
        return render(request, "pong/delete_friends.html", {
                                                'error_message' : {
                                                                        'value' : False,
                                                                        'message' : "nothing"
                                                                }
                                            })







