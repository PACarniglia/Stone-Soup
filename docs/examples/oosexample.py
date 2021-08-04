from stonesoup.types.detection import  Detection
from stonesoup.types.state import State, GaussianState
from stonesoup.feeder.base import DetectionFeeder
from stonesoup.base import Property, Base
from stonesoup.buffered_generator import BufferedGenerator
from stonesoup.tracker.prebuilttrackers import PreBuiltSingleTargetTrackerNoClutter
from stonesoup.models.transition.linear import (
    ConstantVelocity,
    CombinedLinearGaussianTransitionModel
)
import numpy as np
from datetime import datetime, timedelta
from stonesoup.models.measurement.linear import LinearGaussian
from stonesoup.tracker.delayed import FastForwardOldTracker


class SimpleDetectionFeeder(DetectionFeeder):

    detections: list = Property(doc="hello")
    reader = Property(list, default=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.det_iter = iter(self.detections)

    @BufferedGenerator.generator_method
    def data_gen(self):
        for detection in self.detections:
            print("")
            print('release detection', detection.metadata['id'])
            if detection.metadata['id'] == 13:
                five = 5
            yield detection.timestamp, {detection}


'''
The scenario is that we have two sensors producing detections for a tracker. Sensor 1 is close to the tracker and can 
supply detections. Sensor is remote and further away the tracker. There is a delay in the detections from Sensor 2 
reaching the tracker. The delay in the detections is given by the ‘time_delay’ variable.
'''
start_time = datetime.now()

time_delay = 4.5  # seconds

seconds_in_sim = 10


# The target is moving from the origin (0,0,0) north towards (0,x,0) at one unit per second.
def get_target_position(target_time):
    time_since_start = target_time - start_time
    return [0, time_since_start.total_seconds(), 0]


measurement_model = LinearGaussian(
    ndim_state=6,  # Number of state dimensions (position and velocity in 3D)
    mapping=(0, 2, 4),  # Mapping measurement vector index to state index
    noise_covar=np.diag([5]*3)  # Covariance matrix for Gaussian PDF
    )

sensor_1_offset = [-1, 0, 0]

sensor_1_detections = []
sensor_2_detections = []

for idx, time in enumerate([start_time + timedelta(seconds=x) for x in range(seconds_in_sim)]):
    target_pos = get_target_position(time)

    sensor_1_detections.append(Detection(state_vector=[x+y for x, y in zip(target_pos, sensor_1_offset)],
                                         timestamp=time,
                                         measurement_model=measurement_model,
                                         metadata={'Origin': 1,
                                                   'id': idx*2,
                                                   'time_at_tracker': time}))
    sensor_2_detections.append(Detection(state_vector=target_pos, timestamp=time + timedelta(seconds=0.5),
                                         measurement_model=measurement_model,
                                         metadata={'Origin': 2,
                                                   'id': (idx*2)+1,
                                                   'time_at_tracker': time + timedelta(seconds=time_delay)}))


all_detections = [*sensor_1_detections, *sensor_2_detections]


motion_model_noise=0.01
target_transition_model = CombinedLinearGaussianTransitionModel(
    (ConstantVelocity(motion_model_noise), ConstantVelocity(motion_model_noise),
     ConstantVelocity(motion_model_noise)))
ground_truth_prior=GaussianState(state_vector=[1,0,0,1,0,0],timestamp=start_time,covar=np.diag([5]*6))

from stonesoup.plotter import Plotter
plotter = Plotter()
from matplotlib import pyplot as plt
plotter.plot_measurements(all_detections, [0, 2])
plotter.fig

if False:
    tracker_template = PreBuiltSingleTargetTrackerNoClutter(detector=SimpleDetectionFeeder(detections=all_detections),
                                                            ground_truth_prior=ground_truth_prior,
                                                            target_transition_model=target_transition_model)
    tracker = tracker_template.tracker
    for time, track in tracker:
        pass




    plotter.plot_tracks(tracker.tracks, [0, 2], uncertainty=True)
    plotter.fig


    #plt.draw()
    #plt.show()



detections_reordered = list(all_detections)

detections_reordered = sorted(detections_reordered, key=lambda x: x.metadata['time_at_tracker'])



tracker_template = PreBuiltSingleTargetTrackerNoClutter(detector=SimpleDetectionFeeder(detections=detections_reordered),
                                                        ground_truth_prior=ground_truth_prior,
                                                        target_transition_model=target_transition_model)
tracker2 = FastForwardOldTracker(base_tracker=tracker_template.tracker, time_cut_off=timedelta(seconds=5),debug_tracker=True)


#plt.ion()

for time, track in tracker2:
    tracker_show = tracker2.base_tracker
    time_label = "time=" + str((time-start_time).total_seconds()) + "s"
    if False:  # len(tracker_show.tracks) > 0:
        plotter.plot_tracks(tracker_show.tracks, [0, 2], uncertainty=False, track_label="New Track at "+time_label)
        plotter.fig

        plt.show(block=False)
        plt.pause(0.2)


    tracker_show = tracker2.delayed_tracker
    if False:  # len(tracker_show.tracks) > 0:
        plotter.plot_tracks(tracker_show.tracks, [0, 2], uncertainty=False, track_label="Delayed Track at "+time_label)
        plotter.fig

        plt.show(block=False)
        plt.pause(0.2)


    tracker_show = tracker2.base_tracker
    if len(tracker_show.tracks) > 0:
        plotter.plot_tracks(track, [0, 2], uncertainty=False, track_label="Current Track at "+time_label)
        plotter.fig

        plt.show(block=False)
        plt.pause(1.2)



plotter.plot_tracks(tracker2.track_history, [0, 2], uncertainty=False)
plotter.fig

plt.draw()
plt.show()


five=5