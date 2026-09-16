import asyncio

from sensum import Modality, SensoryEvent, SensumRuntime, StateChange, ThresholdAttention
from sensum.sensors import ManualSensor


async def main() -> None:
    sensor = ManualSensor()
    runtime = SensumRuntime(attention=ThresholdAttention(threshold=0.55)).add_sensor(sensor)
    await runtime.start()

    await sensor.emit(
        SensoryEvent(
            kind="payment.completed",
            source="demo",
            modality=Modality.API,
            entity="payment:42",
            summary="Payment 42 completed",
            changes=[StateChange("status", "pending", "completed")],
            novelty=0.9,
            urgency=0.7,
            tags=["payment"],
        )
    )

    event = await anext(runtime.events())
    print(event.to_dict())
    print("World:", runtime.world.snapshot())
    await runtime.stop()


asyncio.run(main())
