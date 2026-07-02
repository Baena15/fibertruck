"""
FiberTrack Assignment Service

Algoritmo de asignación inteligente de tickets a técnicos de campo.
Puntúa candidatos combinando proximidad geográfica, carga de trabajo,
disponibilidad y especialidad.
"""
import math
from typing import List, Optional, Tuple
from django.db.models import QuerySet

from tickets.models import TechnicianProfile, Ticket


# Pesos configurables del algoritmo (deben sumar 1.0)
WEIGHTS = {
    'proximity': 0.35,
    'workload': 0.30,
    'availability': 0.20,
    'skill': 0.15,
}

# Mapeo de tipo de ticket a skill requerida
TICKET_TYPE_SKILL = {
    'home_fault': 'home',
    'network_fault': 'network',
    'degradation': 'home',
    'installation': 'installation',
    'maintenance': 'splicing',
}


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula la distancia en kilómetros entre dos puntos (lat, lng).
    """
    if None in (lat1, lng1, lat2, lng2):
        return float('inf')

    R = 6371.0  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def _proximity_score(profile: TechnicianProfile, ticket: Ticket) -> float:
    """
    Puntuación por proximidad: 1.0 si está justo al lado, 0.0 si está muy lejos.
    Usa distancia suavizada con umbral de 50 km.
    """
    tech_loc = profile.current_location
    ticket_loc = ticket.location

    if not tech_loc or not ticket_loc:
        return 0.0

    distance = haversine_distance(tech_loc[0], tech_loc[1], ticket_loc[0], ticket_loc[1])
    threshold_km = 50.0
    score = max(0.0, 1.0 - (distance / threshold_km))
    return score


def _workload_score(profile: TechnicianProfile) -> float:
    """
    Puntuación por carga de trabajo: 1.0 sin carga, 0.0 si está sobrecargado.
    """
    active = profile.active_ticket_count
    max_load = max(profile.max_workload, 1)

    if profile.is_overloaded:
        return 0.0

    score = max(0.0, 1.0 - (active / max_load))
    return score


def _availability_score(profile: TechnicianProfile) -> float:
    """
    Puntuación por disponibilidad: 1.0 disponible, 0.0 no disponible.
    """
    return 1.0 if profile.is_available else 0.0


def _skill_score(profile: TechnicianProfile, ticket: Ticket) -> float:
    """
    Puntuación por especialidad: 1.0 si el técnico tiene la skill requerida,
    0.5 si tiene alguna skill, 0.0 si no tiene skills definidas.
    """
    required = TICKET_TYPE_SKILL.get(ticket.ticket_type)
    skills = profile.skills or []

    if not required:
        return 0.5

    if required in skills:
        return 1.0

    return 0.5 if skills else 0.0


def score_technician(profile: TechnicianProfile, ticket: Ticket) -> Tuple[float, dict]:
    """
    Calcula la puntuación total (0-100) y devuelve el desglose.
    """
    proximity = _proximity_score(profile, ticket)
    workload = _workload_score(profile)
    availability = _availability_score(profile)
    skill = _skill_score(profile, ticket)

    total = (
        proximity * WEIGHTS['proximity'] +
        workload * WEIGHTS['workload'] +
        availability * WEIGHTS['availability'] +
        skill * WEIGHTS['skill']
    ) * 100.0

    breakdown = {
        'proximity': round(proximity * WEIGHTS['proximity'] * 100, 1),
        'workload': round(workload * WEIGHTS['workload'] * 100, 1),
        'availability': round(availability * WEIGHTS['availability'] * 100, 1),
        'skill': round(skill * WEIGHTS['skill'] * 100, 1),
    }

    return round(total, 1), breakdown


def suggest_technicians(
    ticket: Ticket,
    limit: int = 3,
    queryset: Optional[QuerySet] = None
) -> List[dict]:
    """
    Devuelve una lista ordenada de técnicos recomendados para un ticket.

    Cada elemento incluye:
        - user_id, name, username
        - distance_km
        - active_tickets, max_workload
        - skills, is_available
        - score (0-100)
        - breakdown (desglose por factor)
        - reason (texto explicativo corto)
    """
    if queryset is None:
        queryset = TechnicianProfile.objects.select_related('user').filter(
            user__is_active=True
        )

    candidates = []
    for profile in queryset:
        score, breakdown = score_technician(profile, ticket)

        tech_loc = profile.current_location
        ticket_loc = ticket.location
        distance = None
        if tech_loc and ticket_loc:
            distance = round(haversine_distance(
                tech_loc[0], tech_loc[1], ticket_loc[0], ticket_loc[1]
            ), 2)

        reason_parts = []
        if breakdown['proximity'] >= 30:
            reason_parts.append('cercano')
        if breakdown['workload'] >= 20:
            reason_parts.append('con carga baja')
        if breakdown['skill'] >= 10:
            reason_parts.append('con skill adecuada')
        if not profile.is_available:
            reason_parts.append('(no disponible)')

        candidates.append({
            'user_id': profile.user.id,
            'username': profile.user.username,
            'name': profile.user.get_full_name() or profile.user.username,
            'distance_km': distance,
            'active_tickets': profile.active_ticket_count,
            'max_workload': profile.max_workload,
            'skills': profile.skills,
            'is_available': profile.is_available,
            'score': score,
            'breakdown': breakdown,
            'reason': ', '.join(reason_parts) if reason_parts else 'candidato',
        })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:limit]
