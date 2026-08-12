from rest_framework import serializers
from .models import Booking_Request, LSA_Profile


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking_Request
        fields = [
            "parent",
            "lsa",
            "booking_date",
            "start_time",
            "end_time",
        ]

    def validate(self, attrs):
        if attrs["end_time"] <= attrs["start_time"]:
            raise serializers.ValidationError(
                {"end_time": "end_time must be later than start_time."}
            )
        return attrs


class LSASearchSerializer(serializers.ModelSerializer):
    skills = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = LSA_Profile
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "hourly_rate",
            "skills",
        ]
