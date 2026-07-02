"""
Tests del algoritmo de asignación inteligente de técnicos.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from network.models import Zone, OLT, Splitter, FiberBox, Client
from tickets.models import TechnicianProfile, Ticket
from tickets.services.assignment import (
    haversine_distance, score_technician, suggest_technicians
)


User = get_user_model()


class HaversineDistanceTests(TestCase):
    def test_same_point_zero_distance(self):
        self.assertEqual(haversine_distance(38.239, -1.417, 38.239, -1.417), 0.0)

    def test_known_distance(self):
        # Madrid - Toledo aproximadamente 68 km
        distance = haversine_distance(40.4168, -3.7038, 39.8628, -4.0273)
        self.assertAlmostEqual(distance, 68.0, delta=5.0)

    def test_missing_coordinates(self):
        self.assertEqual(haversine_distance(None, -1.4, 38.2, -1.4), float('inf'))


class AssignmentScoreTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(code='Z-TEST', name='Zona Test', latitude=38.0, longitude=-1.4)
        self.olt = OLT.objects.create(code='OLT-TEST', name='OLT Test', latitude=38.0, longitude=-1.4)
        self.splitter = Splitter.objects.create(
            code='SPL-TEST', name='Splitter Test', ratio='1x8',
            olt=self.olt, zone=self.zone, latitude=38.0, longitude=-1.4, input_port_olt=1
        )
        self.box = FiberBox.objects.create(
            code='CTO-TEST', name='Caja Test', splitter=self.splitter,
            zone=self.zone, latitude=38.001, longitude=-1.401, splitter_port=1
        )
        self.client = Client.objects.create(
            client_code='CLI-001', full_name='Ana García', box=self.box, box_port=1,
            status='active', latitude=38.0011, longitude=-1.4011
        )

        self.coordinator = User.objects.create_user(
            'supervisor1', password='super123', first_name='Supervisor', role='supervisor'
        )
        self.technician = User.objects.create_user(
            'tecnico1', password='tecno123', first_name='Técnico', last_name='Uno', role='technician'
        )
        self.profile = TechnicianProfile.objects.get(user=self.technician)
        self.profile.skills = ['home']
        self.profile.current_latitude = 38.001
        self.profile.current_longitude = -1.401
        self.profile.is_available = True
        self.profile.save()

        self.ticket = Ticket.objects.create(
            title='Avería domicilio',
            description='Cliente sin servicio',
            ticket_type='home_fault',
            priority='high',
            client=self.client,
            affected_box=self.box,
            address='Calle Test 1',
            latitude=38.001,
            longitude=-1.401,
            coordinator=self.coordinator,
            sla_hours=8
        )

    def test_perfect_candidate_scores_high(self):
        score, breakdown = score_technician(self.profile, self.ticket)
        self.assertGreaterEqual(score, 85.0)
        self.assertEqual(breakdown['availability'], 20.0)
        self.assertEqual(breakdown['skill'], 15.0)
        self.assertGreater(breakdown['proximity'], 30.0)

    def test_unavailable_technician_scores_low(self):
        self.profile.is_available = False
        self.profile.save()
        score, _ = score_technician(self.profile, self.ticket)
        self.assertLess(score, 85.0)

    def test_overloaded_technician_scores_low(self):
        self.profile.max_workload = 1
        # Creamos un ticket asignado para sobrecargarlo
        Ticket.objects.create(
            title='Otro ticket',
            ticket_type='home_fault',
            status='assigned',
            assigned_to=self.technician,
            coordinator=self.coordinator,
            sla_hours=24
        )
        score, _ = score_technician(self.profile, self.ticket)
        self.assertLessEqual(score, 70.0)

    def test_suggest_returns_ordered_list(self):
        tech2 = User.objects.create_user('tecnico2', password='tecno123', first_name='Técnico', last_name='Dos', role='technician')
        profile2 = TechnicianProfile.objects.get(user=tech2)
        profile2.skills = ['network']
        profile2.current_latitude = 38.5
        profile2.current_longitude = -1.8
        profile2.is_available = True
        profile2.save()

        suggestions = suggest_technicians(self.ticket, limit=2)
        self.assertEqual(len(suggestions), 2)
        self.assertGreater(suggestions[0]['score'], suggestions[1]['score'])
        self.assertEqual(suggestions[0]['user_id'], self.technician.id)

    def test_suggest_excludes_inactive_users(self):
        self.technician.is_active = False
        self.technician.save()
        suggestions = suggest_technicians(self.ticket)
        self.assertEqual(len(suggestions), 0)
