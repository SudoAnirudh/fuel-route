from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

from fuel_routes.serializers import (
    RoutePlanRequestSerializer,
    RoutePlanResponseSerializer
)
from fuel_routes.services.planner import PlannerService


class RoutePlanView(APIView):
    """
    Plan an optimal fuel route between a U.S. start and finish location.
    Calculates distance, geometry, fuel stops, and total cost using Decimal arithmetic.
    """
    @extend_schema(
        summary="Plan Fuel Route",
        description="Calculates a cost-effective driving route and fuel stop plan between two U.S. locations.",
        request=RoutePlanRequestSerializer,
        responses={
            200: OpenApiResponse(response=RoutePlanResponseSerializer, description="Route plan generated successfully"),
            400: OpenApiResponse(description="Validation error (invalid input or non-U.S. locations)"),
            422: OpenApiResponse(description="Unprocessable Entity (no feasible fuel plan satisfies range)"),
            500: OpenApiResponse(description="Internal server error")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = RoutePlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start = serializer.validated_data["start"]
        finish = serializer.validated_data["finish"]

        planner = PlannerService()
        result = planner.plan_route(start_location=start, finish_location=finish)

        return Response(result, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    Health check endpoint for container orchestrators and monitoring.
    """
    @extend_schema(
        summary="Health Check",
        description="Returns system and database connectivity health status.",
        responses={200: OpenApiResponse(description="System is healthy")}
    )
    def get(self, request, *args, **kwargs):
        db_status = "healthy"
        try:
            connection.ensure_connection()
        except Exception:
            db_status = "unhealthy"

        return Response(
            {
                "status": "ok",
                "database": db_status
            },
            status=status.HTTP_200_OK if db_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        )
