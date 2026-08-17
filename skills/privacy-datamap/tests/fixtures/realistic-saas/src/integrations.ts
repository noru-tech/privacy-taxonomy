import Hubspot from "@hubspot/api-client";
import * as Sentry from "@sentry/node";
import OpenAI from "openai";
import Stripe from "stripe";

export const calendars = [
  "https://calendar.googleapis.com/calendar/v3",
  "https://graph.microsoft.com/v1.0/me/calendars",
];
