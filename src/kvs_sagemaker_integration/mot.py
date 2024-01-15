import numpy as np
from sort import Sort as _Sort
from logger import Logger

logger = Logger(__name__).get()


def _tracker_to_label(tracker, width, height):
    left, top, right, bottom, tracking = tracker
    label = dict(
        left=int(np.clip(left, 0, width)),
        top=int(np.clip(top, 0, height)),
        right=int(np.clip(right, 0, width)),
        bottom=int(np.clip(bottom, 0, height)),
        tracking=int(tracking)
    )
    return label


def _labels_to_detections(labels):
    detections = list()
    for label in labels:
        detection = [label.get('left'), label.get('top'), label.get('right'), label.get('bottom'), label.get('confidence')]
        detections.append(detection)
    detections = np.array(detections)
    return detections


class Tracker:
    def __init__(self, max_age=20, min_hits=20, iou_threshold=0.1):
        self.mot_tracker = _Sort(max_age, min_hits, iou_threshold)
        # self._record = dict()

    # @property
    # def record(self):
    #     return self._record

    def update(self, frame):
        items = []
        height, width, _ = frame.img.shape
        detections = _labels_to_detections(frame.labels)
        trackers = self.mot_tracker.update(detections).tolist()[::-1]
        for label, tracker in zip(frame.labels, trackers):
            label.update(_tracker_to_label(tracker, width, height))
            # if 'id' in label and 'tracking' in label and label['tracking'] not in self._record:
            # self._record.update({label['tracking']: label['id']})
            item = {"id": label['id'], "tracking": label['tracking']}
            items.append(item)
        return items

