from tests.base import ApiTestCase


class ServiceTicketTests(ApiTestCase):
    def test_create_edit_mechanics_and_add_part(self):
        created_ticket = self.client.post(
            "/service-tickets/",
            headers=self.customer_headers(),
            json={"description": "Replace front brakes"},
        )
        self.assertEqual(created_ticket.status_code, 201)
        ticket_id = created_ticket.get_json()["id"]

        mechanic_headers = self.mechanic_headers()
        created_part = self.client.post(
            "/inventory/",
            headers=mechanic_headers,
            json={"name": "Front Brake Pads", "price": 89.50},
        )
        part_id = created_part.get_json()["id"]

        edited = self.client.put(
            f"/service-tickets/{ticket_id}/edit",
            headers=mechanic_headers,
            json={"add_ids": [self.mechanic_id], "remove_ids": []},
        )
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.get_json()["added_ids"], [self.mechanic_id])

        part_added = self.client.put(
            f"/service-tickets/{ticket_id}/add-part/{part_id}",
            headers=mechanic_headers,
        )
        self.assertEqual(part_added.status_code, 200)
        self.assertEqual(len(part_added.get_json()["ticket"]["parts"]), 1)

        updated = self.client.put(
            f"/service-tickets/{ticket_id}",
            headers=mechanic_headers,
            json={"status": "In Progress"},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["status"], "In Progress")
