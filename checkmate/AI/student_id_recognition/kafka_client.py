"""
Kafka 통신 모듈
"""
import logging
from typing import Optional

# Kafka는 선택적 import
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    # KafkaProducer가 없을 경우를 위한 타입 힌트
    KafkaProducer = type(None)


def send_kafka_status(
    producer: Optional[KafkaProducer],
    student_id_recognition_topic: str,
    status: str,
    low_confidence_images: Optional[list] = None
) -> None:
    """
    Kafka로 상태 메시지 전송 (새로운 형식).
    
    Args:
        producer: Kafka Producer 객체
        student_id_recognition_topic: Kafka 토픽명
        status: 상태 ("PENDING" 또는 "DONE")
        low_confidence_images: 낮은 신뢰도 이미지 리스트 (DONE일 때만 사용)
    """
    if not producer or not KAFKA_AVAILABLE:
        return
    
    try:
        if status == "PENDING":
            message = {"status": "PENDING"}
        elif status == "DONE":
            message = {
                "status": "DONE",
                "lowConfidenceImages": low_confidence_images if low_confidence_images is not None else []
            }
        else:
            logging.getLogger(__name__).warning(f"Unknown status: {status}")
            return
        
        # 딕셔너리를 직접 전송 (value_serializer가 자동으로 JSON으로 변환)
        producer.send(student_id_recognition_topic, message)
        
        if status == "DONE":
            producer.flush()
    
    except Exception as e:
        logging.getLogger(__name__).warning(f"Kafka status send failed: {e}")

