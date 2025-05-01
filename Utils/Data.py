from datetime import datetime, time
import pytz


def tz():
    return pytz.timezone('America/Sao_Paulo')


def current_date():
    return datetime.now(tz())


def new_update():
    
    dt = current_date().strftime('%Y-%m-%d %H:%M:%S')

    with open('up.txt', 'w') as up:
        up.write(dt)
        return True


def last_update():
    
    try:
        with open('up.txt', 'r') as up:
            return datetime.strptime(up.read(), '%Y-%m-%d %H:%M:%S').astimezone(tz()) 

    except:
        return datetime(2000,1,1,0,0,0,0,tzinfo=tz())


def horario_atualizacao(hora, minuto):

    dia = current_date().date()
    hora = time(hour=hora, minute=minuto, tzinfo=tz())
    return datetime.combine(dia, hora)


def need_update(*args):
    
    for hora, minuto in args:

        if last_update() < horario_atualizacao(hora, minuto) and current_date() > horario_atualizacao(hora, minuto): return True
    
    return False