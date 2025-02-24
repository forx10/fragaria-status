from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegistroForm, LoginForm
from django.core.mail import send_mail
from django.contrib.auth.forms import PasswordResetForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .forms import SetPasswordForm 
from django.contrib.auth import get_user_model
from .forms import UsuarioForm  
from django.http import HttpResponseForbidden
from .models import Usuario
import requests
from django.http import JsonResponse
from datetime import datetime
from .models import Plantacion, Siembra
from .forms import PlantacionForm, RegistroForm
from .models import Usuario, FechasSiembra
from django.shortcuts import render, redirect
from .models import Actividad, EstadoActividad
from .forms import ActividadForm, EstadoActividadForm
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes
import json





def inicio(request):
    return render(request, 'usuarios/base.html')  


def mi_vista(request):
    messages.success(request, "¡Operación completada correctamente!")
    return redirect('nombre_de_la_url')


@csrf_exempt
def iniciar_sesion(request):
    if request.method == 'POST':
        try:
            # Verificar si el cuerpo de la solicitud está vacío
            if not request.body:
                return JsonResponse({
                    'status': 400,
                    'success': False,
                    'message': 'Cuerpo de la solicitud vacío'
                })

            # Decodificar el cuerpo de la solicitud a JSON
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formato JSON inválido'
            })

        # Validar el formulario con los datos del JSON
        form = LoginForm(data)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Autenticar al usuario
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)

                # Redirigir según el tipo de usuario
                if user.is_superuser:
                    return JsonResponse({
                        'status': 200,
                        'success': True,
                        'redirect_url': 'usuarios/dashboard_admin.html'
                    })
                elif user.is_staff:
                    return JsonResponse({
                        'status': 200,
                        'success': True,
                        'redirect_url': 'usuarios/admin_dashboard_limited.html'
                    })
                else:
                    return JsonResponse({
                        'status': 200,
                        'success': True,
                        'redirect_url': 'usuarios/inicio.html'
                    })
            else:
                return JsonResponse({
                    'status': 400,
                    'success': False,
                    'message': 'Datos incorrectos'
                })
        else:
            # Devolver errores de validación del formulario
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido',
                'errors': errors
            })
    else:
        # Si la solicitud no es POST, devolver un error
        return JsonResponse({
            'status': 405,
            'success': False,
            'message': 'Método no permitido'
        })




@login_required
def admin_dashboard_limited(request):
    ubicacion = 'Pereira'
    clima_data = obtener_clima(ubicacion)

    # Simplificar la asignación de variables relacionadas con el clima
    temperatura = clima_data.get('temperatura') if clima_data else None
    descripcion = clima_data.get('descripcion') if clima_data else None
    humedad = clima_data.get('humedad') if clima_data else None
    presion = clima_data.get('presion') if clima_data else None
    velocidad_viento = clima_data.get('velocidad_viento') if clima_data else None
    
    return render(request,'usuarios/admin_dashboard_limited.html', {
        'temperatura': temperatura,
        'descripcion': descripcion,
        'humedad': humedad,
        'presion': presion,
        'velocidad_viento': velocidad_viento,
        'ubicacion': ubicacion,
    })
    
    
@login_required
def dashboard_admin(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    usuarios = Usuario.objects.all()
    total_usuarios = usuarios.count()
    total_proyectos = 5  # Ejemplo, reemplaza con lógica real

    context = {
        'user': request.user,
        'usuarios': usuarios,
        'total_usuarios': total_usuarios,
        'total_proyectos': total_proyectos,
    }
    ubicacion = 'Pereira'
    clima_data = obtener_clima(ubicacion)

    # Simplificar la asignación de variables relacionadas con el clima
    temperatura = clima_data.get('temperatura') if clima_data else None
    descripcion = clima_data.get('descripcion') if clima_data else None
    humedad = clima_data.get('humedad') if clima_data else None
    presion = clima_data.get('presion') if clima_data else None
    velocidad_viento = clima_data.get('velocidad_viento') if clima_data else None
    
    return render(request,'usuarios/admin_dashboard_limited.html', context, {
        'temperatura': temperatura,
        'descripcion': descripcion,
        'humedad': humedad,
        'presion': presion,
        'velocidad_viento': velocidad_viento,
        'ubicacion': ubicacion,
    })

#Se verifica si el login cuenta con credenciales creadas mediante superUser, si es el caso, se valida y tiene acceso a los empleados 





@csrf_exempt
def login_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = LoginForm(data)
            if form.is_valid():
                user = form.get_user()
                if user.is_staff:  # Verificamos si es un administrador
                    login(request, user)
                    return JsonResponse({
                        'status': 200,
                        'success': True,
                        'message': 'Bienvenido administrador.',
                        'redirect_url': 'gestion_usuarios'
                    })
                else:
                    return JsonResponse({
                        'status': 403,
                        'success': False,
                        'message': 'No tienes permisos de administrador.'
                    }, status=403)
            else:
                errors = form.errors.as_json()
                return JsonResponse({
                    'status': 400,
                    'success': False,
                    'message': 'Formulario inválido.',
                    'errors': errors
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formato JSON inválido.'
            }, status=400)
    else:
        return JsonResponse({
            'status': 405,
            'success': False,
            'message': 'Método no permitido.'
        }, status=405)


#Vista que permite la gestion de usuarios via administrador


@login_required
def gestion_usuarios(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    usuarios = Usuario.objects.filter(admin_creator = request.user)  # Obtén todos los usuarios

    return render(request, 'usuarios/gestion_usuarios.html', {'usuarios': usuarios})


#Vista que permite agregar usuarios via administrador



# necesita cambios con status (no sé completamente la verdad, pero podría ser que si)

@login_required
def agregar_usuario(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.is_staff = False
            user.admin_creator = request.user
            user.save()
            messages.success(request, "Usuario creado exitosamente.")
            return redirect('gestion_usuarios')
    else:
        form = RegistroForm()

    return render(request, 'usuarios/agregar_usuario.html', {'form': form})


#Vista que permite editar usuarios via administrador



@login_required
def editar_usuario(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({
            'status': 403,
            'success': False,
            'message': 'No tienes permiso para acceder a esta página.'
        }, status=403)

    usuario = get_object_or_404(Usuario, id=user_id)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Usuario actualizado exitosamente.',
                'redirect_url': 'gestion_usuarios'
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido.',
                'errors': errors
            }, status=400)
    else:
        form = UsuarioForm(instance=usuario)
        return render(request, 'usuarios/editar_usuario.html', {'form': form, 'usuario': usuario})


#Vista que permite eliminar usuarios via administrador

@login_required
def eliminar_usuario(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({
            'status': 403,
            'success': False,
            'message': 'No tienes permiso para acceder a esta página.'
        }, status=403)

    usuario = get_object_or_404(Usuario, id=user_id)

    if request.method == 'POST':
        try:
            usuario.actividades.clear()
            usuario.plantacion = None
            FechasSiembra.objects.filter(usuario=usuario).delete()
            usuario.delete()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': f"El usuario {usuario.first_name} {usuario.last_name} ha sido eliminado exitosamente.",
                'redirect_url': 'gestion_usuarios'
            })
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'success': False,
                'message': f"Ocurrió un error al eliminar el usuario: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            'status': 405,
            'success': False,
            'message': 'Método no permitido.'
        }, status=405)



@csrf_exempt
def registro(request):
    if request.method == 'POST':
        
        data = json.loads(request.body)
        form = RegistroForm(data)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.is_staff = True  # Todos los usuarios son staff (administradores)
            user.save()
            login(request, user)
            return JsonResponse({"message": "Registro exitoso."}, status=200)
        else:
            return JsonResponse({"errors": form.errors}, status=400)
    
    return JsonResponse({"message": "Método no permitido."}, status=405)

#Funcion que permite la restauracion de contraseña generando un token y enviandolo via gmail, siempre y cuando el correo registrado este asociado a una cuenta
#de google, de lo contrario,este correo no llegara.

@csrf_exempt
def password_reset_api(request):
    if request.method == "POST":
        User = get_user_model()  # Obtiene el modelo de usuario actual
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"error": "El correo es obligatorio."}, status=400)

            try:
                user = User.objects.get(email=email)
                
                # Generar token y UID
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Crear enlace de restablecimiento
                reset_url = f'http://127.0.0.1:3000/reset-password/{uid}/{token}/'

                # Enviar el correo
                subject = "Restablecimiento de contraseña"
                message = f"Hola {user.username},\n\nPara restablecer tu contraseña, haz clic en este enlace:\n\n{reset_url}\n\nSi no solicitaste este cambio, ignora este mensaje."
                send_mail(subject, message, 'tu_correo@gmail.com', [email])

                return JsonResponse({"message": "Se ha enviado un enlace de recuperación a tu correo."}, status=200)
            except User.DoesNotExist:
                return JsonResponse({"error": "No encontramos una cuenta con ese correo."}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Datos inválidos."}, status=400)

    return JsonResponse({"error": "Método no permitido."}, status=405)


#Redireccion a la pagina mediante enlace enviado via gmail, el cual permite realizar la actualizacion de contraseña y redireccion a login.


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    return JsonResponse({
                        'status': 200,
                        'success': True,
                        'message': 'Tu contraseña ha sido restablecida correctamente.',
                        'redirect_url': 'login'
                    })
                else:
                    errors = form.errors.as_json()
                    return JsonResponse({
                        'status': 400,
                        'success': False,
                        'message': 'Formulario inválido.',
                        'errors': errors
                    }, status=400)
            else:
                form = SetPasswordForm(user)
                return render(request, 'usuarios/reset_password.html', {'form': form})
        else:
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'El enlace de restablecimiento de contraseña no es válido o ha expirado.'
            }, status=400)
    except (TypeError, ValueError, OverflowError, user.DoesNotExist):
        return JsonResponse({
            'status': 400,
            'success': False,
            'message': 'El enlace de restablecimiento de contraseña no es válido o ha expirado.'
        }, status=400)




# Función para obtener las fechas de siembra recomendadas desde una API

def obtener_clima(ubicacion):
    api_key = 'b38f3f8558d7bee2759f548984ae5505'  # Reemplaza con tu clave API
    url = f'https://api.openweathermap.org/data/2.5/weather?q={ubicacion}&appid={api_key}&units=metric'

    # Diccionario de traducciones del clima
    CLIMA_TRADUCCIONES = {
        "Clear": "Despejado",
        "Clouds": "Nublado",
        "Rain": "Lluvia",
        "Drizzle": "Llovizna",
        "Thunderstorm": "Tormenta",
        "Snow": "Nieve",
        "Mist": "Neblina",
        "Smoke": "Humo",
        "Haze": "Bruma",
        "Dust": "Polvo",
        "Fog": "Niebla",
        "Sand": "Arena",
        "Ash": "Ceniza",
        "Squall": "Chubasco",
        "Tornado": "Tornado",
        "light rain": "llovizna",
        "moderate rain": "lluvia moderada",
        "heavy intensity rain": "lluvia intensa",
        "very heavy rain": "lluvia muy intensa",
        "extreme rain": "lluvia extrema",
        "freezing rain": "lluvia helada",
        "thunderstorm": "tormenta",
        "snow": "nieve",
        "mist": "neblina",
        "drizzle": "llovizna",
        "overcast clouds": "nubes cubiertas",
        "scattered clouds": "nubes dispersas",
        "broken clouds": "nubes rotas",
        "few clouds": "pocas nubes"
    }

    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción si hay un error en la respuesta
        data = response.json()  # Convierte la respuesta a JSON

        # Verificar que los datos esperados están en la respuesta
        if "main" in data and "weather" in data:
            # Extraer la información necesaria
            temperatura = data['main']['temp']
            descripcion_ingles = data['weather'][0]['description']
            # Traducir la descripción al español
            descripcion = CLIMA_TRADUCCIONES.get(descripcion_ingles, descripcion_ingles)  # Fallback en caso de que no se encuentre
            humedad = data['main']['humidity']
            presion = data['main']['pressure']
            velocidad_viento = data['wind']['speed']
            return {
                'temperatura': temperatura,
                'descripcion': descripcion,
                'humedad': humedad,
                'presion': presion,
                'velocidad_viento': velocidad_viento
            }
        else:
            print("La respuesta no contiene los datos esperados:", data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos del clima: {e}")
        return None
    
    



# Vista para mostrar todas las plantaciones
@login_required
def plantacion(request):
    
    plantaciones = Plantacion.objects.filter(usuario=request.user)
    # return render(request, 'usuarios/plantaciones.html', {'plantaciones': plantaciones})
    ubicacion = 'Pereira'
    clima_data = obtener_clima(ubicacion)

    # Simplificar la asignación de variables relacionadas con el clima
    temperatura = clima_data.get('temperatura') if clima_data else None
    descripcion = clima_data.get('descripcion') if clima_data else None
    humedad = clima_data.get('humedad') if clima_data else None
    presion = clima_data.get('presion') if clima_data else None
    velocidad_viento = clima_data.get('velocidad_viento') if clima_data else None
    
    return render(request,'usuarios/plantaciones.html', {'plantaciones': plantaciones, 
        'temperatura': temperatura,
        'descripcion': descripcion,
        'humedad': humedad,
        'presion': presion,
        'velocidad_viento': velocidad_viento,
        'ubicacion': ubicacion,
    })
    

TRADUCCION_CLIMA = {
        "Clear": "Despejado",
        "Clouds": "Nublado",
        "Rain": "Lluvia",
        "Drizzle": "Llovizna",
        "Thunderstorm": "Tormenta",
        "Snow": "Nieve",
        "Mist": "Neblina",
        "Smoke": "Humo",
        "Haze": "Bruma",
        "Dust": "Polvo",
        "Fog": "Niebla",
        "Sand": "Arena",
        "Ash": "Ceniza",
        "Squall": "Chubasco",
        "Tornado": "Tornado",
        "light rain": "llovizna",
        "moderate rain": "lluvia moderada",
        "heavy intensity rain": "lluvia intensa",
        "very heavy rain": "lluvia muy intensa",
        "extreme rain": "lluvia extrema",
        "freezing rain": "lluvia helada",
        "thunderstorm": "tormenta",
        "snow": "nieve",
        "mist": "neblina",
        "drizzle": "llovizna",
        "overcast clouds": "nubes cubiertas",
        "scattered clouds": "nubes dispersas",
        "broken clouds": "nubes rotas",
        "few clouds": "pocas nubes"
}







# necesita cambios con status
# Vista para registrar una nueva plantación
@login_required
def registrar_plantacion(request):
    # Configuración de la API del clima
    API_KEY = 'b38f3f8558d7bee2759f548984ae5505'  # Reemplaza con tu clave API
    ubicacion = 'Pereira,CO'
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={ubicacion}&appid={API_KEY}&units=metric"

    # Obtener datos del clima
    response = requests.get(url)
    if response.status_code != 200:
        messages.error(request, 'No se pudo obtener el clima. Inténtalo de nuevo más tarde.')
        return render(request, 'usuarios/registrar_plantacion.html', {'form': PlantacionForm()})

    clima_data = response.json()
    fechas_recomendadas = []

    # Filtrar fechas con clima templado
    for pronostico in clima_data['list']:
        fecha = pronostico['dt_txt']  # Fecha en formato 'año-mes-dia h:min:seg'
        temperatura = pronostico['main']['temp']
        if 15 <= temperatura <= 25:  # Rango de clima templado
            fecha_formateada = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            if fecha_formateada not in fechas_recomendadas:  # Evitar duplicados
                fechas_recomendadas.append(fecha_formateada)

    # Obtener el clima actual
    clima_actual_url = f"http://api.openweathermap.org/data/2.5/weather?q={ubicacion}&appid={API_KEY}&units=metric"
    clima_actual_response = requests.get(clima_actual_url)
    if clima_actual_response.status_code == 200:
        clima_actual_data = clima_actual_response.json()
        temperatura_actual = clima_actual_data['main']['temp']
        descripcion_ingles = clima_actual_data['weather'][0]['description']
        descripcion_actual = TRADUCCION_CLIMA.get(descripcion_ingles, descripcion_ingles)
        humedad_actual = clima_actual_data['main']['humidity']
        presion_actual = clima_actual_data['main']['pressure']
        velocidad_viento_actual = clima_actual_data['wind']['speed']
    else:
        temperatura_actual = descripcion_actual = humedad_actual = presion_actual = velocidad_viento_actual = None

    # solicitudes POST estoy cansadoooooo jaja erdaa con tanta cosa por hacer y nos las estoy haciendo bien por estar pensando si estás bien.
    if request.method == 'POST':
        form = PlantacionForm(request.POST)
        if form.is_valid():
            plantacion = form.save(commit=False)
            plantacion.usuario = request.user
            fecha_recomendada = request.POST.get('fecha_recomendada')
            fecha_personalizada = request.POST.get('fecha_personalizada')

            if fecha_personalizada:
                plantacion.fecha_siembra = fecha_personalizada
            elif fecha_recomendada:
                plantacion.fecha_siembra = fecha_recomendada
            else:
                return JsonResponse({
                    'status': 400,
                    'success': False,
                    'message': 'Debes seleccionar una fecha de siembra.'
                }, status=400)

            plantacion.save()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Plantación registrada correctamente.',
                'redirect_url': 'plantaciones'
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido.',
                'errors': errors
            }, status=400)

    # solicitudes GET
    else:
        form = PlantacionForm()
        return render(request, 'usuarios/registrar_plantacion.html', {
            'form': form,
            'fechas_recomendadas': fechas_recomendadas,
            'temperatura': temperatura_actual,
            'descripcion': descripcion_actual,
            'humedad': humedad_actual,
            'presion': presion_actual,
            'velocidad_viento': velocidad_viento_actual,
            'ubicacion': ubicacion,
        })           


        
        
        
        

def registrar_actividad(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save()
            estado = EstadoActividad(estado="Pendiente", actividad=actividad)
            estado.save()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Actividad registrada correctamente.',
                'redirect_url': 'lista_actividades'
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido.',
                'errors': errors
            }, status=400)
    else:
        form = ActividadForm()
        return render(request, 'registrar_actividad.html', {'form': form})





def registrar_estado_actividad(request, actividad_id):
    actividad = get_object_or_404(Actividad, id=actividad_id)
    if request.method == 'POST':
        form = EstadoActividadForm(request.POST)
        if form.is_valid():
            estado = form.save(commit=False)
            estado.actividad = actividad
            estado.save()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Estado de la actividad registrado correctamente.',
                'redirect_url': 'lista_actividades'
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido.',
                'errors': errors
            }, status=400)
    else:
        form = EstadoActividadForm()
        return render(request, 'actividades/registrar_estado_actividad.html', {'form': form, 'actividad': actividad})



def cronograma(request):
    # Aquí puedes filtrar las actividades según la fecha, el estado, etc.
    actividades = Actividad.objects.all()  # O filtra según algún criterio específico, como fechas

    context = {
        'actividades': actividades,
    }
    
    return render(request, 'usuarios/cronograma.html', context)



@login_required
def informes(request):
    """
    Vista para mostrar los informes.
    Solo usuarios autenticados pueden acceder.
    """
    context = {
        'user': request.user,
        'message': 'Aquí puedes ver los informes generados.',
    }
    return render(request, 'usuarios/informes.html', context)



@login_required
def listar_plantaciones(request):
    plantaciones = Plantacion.objects.all()  
    return render(request, 'usuarios/plantaciones.html', {'plantaciones': plantaciones})


@login_required
def editar_plantacion(request, id):
    plantacion = get_object_or_404(Plantacion, id=id)
    if request.method == 'POST':
        form = PlantacionForm(request.POST, instance=plantacion)
        if form.is_valid():
            form.save()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Plantación actualizada correctamente.',
                'redirect_url': 'plantaciones'
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'status': 400,
                'success': False,
                'message': 'Formulario inválido.',
                'errors': errors
            }, status=400)
    else:
        form = PlantacionForm(instance=plantacion)
        return render(request, 'usuarios/editar_plantacion.html', {'form': form})



@login_required
def eliminar_plantacion(request, id):
    plantacion = get_object_or_404(Plantacion, id=id)
    if request.method == 'POST':
        try:
            plantacion.delete()
            return JsonResponse({
                'status': 200,
                'success': True,
                'message': 'Plantación eliminada correctamente.',
                'redirect_url': 'plantaciones'
            })
        except Exception as e:
            return JsonResponse({
                'status': 500,
                'success': False,
                'message': f"Ocurrió un error al eliminar la plantación: {str(e)}"
            }, status=500)
    else:
        return JsonResponse({
            'status': 405,
            'success': False,
            'message': 'Método no permitido.'
        }, status=405)

