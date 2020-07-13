Feature: appointment
  Scenario: next appointment
    Given an English speaking user
     When the user says "What's my next appointment"
     Then "appointment-skill" should reply with dialog from "next-appointment.dialog"