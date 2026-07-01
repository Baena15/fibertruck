"""
FiberTruck - Tests Unitarios del Algoritmo de Diagnostico FTTH

Tests del algoritmo FTFL que encuentra puntos de divergencia:
- Individual -> diagnostico unico
- Misma caja (2+) -> problema en caja
- Mismo splitter (3+) -> bulk outage critico
"""
from django.test import TestCase
from network.models import OLT, Zone, Splitter, FiberBox, Client


class DiagnosisAlgorithmTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(code='Z-TEST', name='Zona Test', latitude=38.0, longitude=-1.4)
        self.olt = OLT.objects.create(code='OLT-TEST', name='OLT Test', latitude=38.0, longitude=-1.4)
        self.splitter = Splitter.objects.create(code='SPL-TEST', name='Splitter Test', ratio='1x8', olt=self.olt, zone=self.zone, latitude=38.0, longitude=-1.4, input_port_olt=1)
        self.box1 = FiberBox.objects.create(code='CTO-TEST1', name='Caja Test 1', splitter=self.splitter, zone=self.zone, latitude=38.001, longitude=-1.401, splitter_port=1)
        self.box2 = FiberBox.objects.create(code='CTO-TEST2', name='Caja Test 2', splitter=self.splitter, zone=self.zone, latitude=38.002, longitude=-1.402, splitter_port=2)
        self.client1 = Client.objects.create(client_code='CLI-001', full_name='Ana Garcia', box=self.box1, box_port=1, status='active', latitude=38.0011, longitude=-1.4011)
        self.client2 = Client.objects.create(client_code='CLI-002', full_name='Pedro Lopez', box=self.box1, box_port=2, status='active', latitude=38.0012, longitude=-1.4012)
        self.client3 = Client.objects.create(client_code='CLI-003', full_name='Maria Ruiz', box=self.box2, box_port=1, status='active', latitude=38.0021, longitude=-1.4021)
        self.client4 = Client.objects.create(client_code='CLI-004', full_name='Juan Martinez', box=self.box2, box_port=2, status='active', latitude=38.0022, longitude=-1.4022)

    def test_hierarchy_structure(self):
        self.assertEqual(OLT.objects.count(), 1)
        self.assertEqual(Splitter.objects.count(), 1)
        self.assertEqual(FiberBox.objects.count(), 2)
        self.assertEqual(Client.objects.count(), 4)

    def test_client_path(self):
        self.assertEqual(self.client1.full_path, 'OLT-TEST > SPL-TEST > CTO-TEST1 > CLI-001')

    def test_box_hierarchy(self):
        self.assertEqual(self.box1.splitter.olt.code, 'OLT-TEST')
        self.assertEqual(self.box1.client_count, 2)

    def test_individual_outage(self):
        self.client1.status = 'affected'
        self.client1.save()
        same_box = Client.objects.filter(box=self.client1.box, status='affected', is_active=True).exclude(id=self.client1.id)
        self.assertEqual(same_box.count(), 0)

    def test_same_box_multiple_affected(self):
        self.client1.status = 'affected'
        self.client1.save()
        self.client2.status = 'affected'
        self.client2.save()
        same_box = Client.objects.filter(box=self.box1, status='affected', is_active=True)
        self.assertEqual(same_box.count(), 2)

    def test_bulk_outage_splitter(self):
        self.client1.status = 'affected'
        self.client1.save()
        self.client2.status = 'affected'
        self.client2.save()
        self.client3.status = 'affected'
        self.client3.save()
        affected = Client.objects.filter(box__splitter=self.splitter, status='affected', is_active=True)
        self.assertEqual(affected.count(), 3)
        affected_boxes = set(affected.values_list('box__code', flat=True))
        self.assertEqual(len(affected_boxes), 2)

    def test_diagnosis_confidence_levels(self):
        levels = {1: 60, 2: 80, 3: 85, 4: 90}
        for count, expected in levels.items():
            Client.objects.all().update(status='active')
            for cl in list(Client.objects.all()[:count]):
                cl.status = 'affected'; cl.save()
            total = Client.objects.filter(box__splitter=self.splitter, status='affected', is_active=True).count()
            if total >= 3: calc = min(85 + (total - 3) * 5, 99)
            elif total >= 2: calc = 75 + (total - 1) * 5
            else: calc = 60
            self.assertEqual(calc, expected)

    def test_outage_restoration(self):
        self.client1.status = 'affected'; self.client1.save()
        self.assertEqual(self.client1.status, 'affected')
        self.client1.status = 'active'; self.client1.save()
        self.assertEqual(self.client1.status, 'active')

    def test_splitter_port_capacity(self):
        self.assertEqual(self.splitter.total_ports, 8)
        self.assertEqual(self.splitter.occupied_ports, 2)
        self.assertEqual(self.splitter.free_ports, 6)

    def test_cascade_affected_count(self):
        self.assertEqual(self.box1.affected_count, 0)
        self.client1.status = 'affected'; self.client1.save()
        self.assertEqual(self.box1.affected_count, 1)

    def test_different_splitters_isolated(self):
        splitter2 = Splitter.objects.create(code='SPL-TEST2', name='Splitter 2', ratio='1x8', olt=self.olt, zone=self.zone, latitude=38.1, longitude=-1.5, input_port_olt=2)
        box3 = FiberBox.objects.create(code='CTO-TEST3', name='Caja 3', splitter=splitter2, zone=self.zone, latitude=38.101, longitude=-1.501, splitter_port=1)
        client5 = Client.objects.create(client_code='CLI-005', full_name='Luis Sanchez', box=box3, box_port=1, status='active', latitude=38.1011, longitude=-1.5011)
        self.client1.status = 'affected'; self.client1.save()
        self.client2.status = 'affected'; self.client2.save()
        self.assertEqual(client5.status, 'active')
        self.assertEqual(Client.objects.filter(box__splitter=self.splitter, status='affected', is_active=True).count(), 2)
        self.assertEqual(Client.objects.filter(box__splitter=splitter2, status='affected', is_active=True).count(), 0)


class ModelStructureTests(TestCase):
    def test_zone_str(self):
        z = Zone.objects.create(code='Z-TEST', name='Test', latitude=38.0, longitude=-1.4)
        self.assertEqual(str(z), 'Z-TEST - Test')

    def test_splitter_port_extraction(self):
        z = Zone.objects.create(code='Z-T', name='Z', latitude=38.0, longitude=-1.4)
        o = OLT.objects.create(code='OLT-01', name='OLT', latitude=38.0, longitude=-1.4)
        s = Splitter.objects.create(code='SPL-01', name='S', ratio='1x32', olt=o, zone=z, latitude=38.0, longitude=-1.4)
        self.assertEqual(s.total_ports, 32)
