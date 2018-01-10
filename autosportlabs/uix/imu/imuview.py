#
# Race Capture App
#
# Copyright (C) 2014-2017 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

import math
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.resources import resource_find
from kivy.properties import ReferenceListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.logger import Logger
from kivy3 import Scene, Renderer, PerspectiveCamera
from kivy3.loaders import OBJLoader
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.label import Label
import os
from utils import is_ios

class ImuView(BoxLayout):
    ACCEL_SCALING = 1.0
    GYRO_SCALING = 1.0
    ZOOM_SCALING = 0.2
    TOUCHWHEEL_ZOOM_MULTIPLIER = 1
    ROTATION_SCALING = 0.2
    DRAG_CUSTOMIZE_THRESHOLD = 10

    position_x = NumericProperty(0)
    position_y = NumericProperty(-0.15)
    position_z = NumericProperty(-5.0)
    rotation_x = NumericProperty(-5)
    rotation_y = NumericProperty(180)
    rotation_z = NumericProperty(0)

    accel_x = NumericProperty(0)
    accel_y = NumericProperty(0)
    accel_z = NumericProperty(0)

    accel = ReferenceListProperty(accel_x, accel_y, accel_z)
    imu_obj = ObjectProperty()

    gyro_yaw = NumericProperty(0)
    gyro_pitch = NumericProperty(0)
    gyro_roll = NumericProperty(0)
    gyro = ReferenceListProperty(gyro_yaw, gyro_pitch, gyro_roll)
    model_path = StringProperty()

    def __init__(self, **kwargs):
        super(ImuView, self).__init__(**kwargs)
        self._touches = []
        self.imu_obj = None
        self.size_scaling = 1
        self.init_view()
        self.register_event_type('on_customize')
        self._total_drag_distance = 0
        self._last_button = None

    def on_customize(self):
        pass

    def init_view(self):
        Window.bind(on_motion=self.on_motion)

    def cleanup_view(self):
        Window.unbind(on_motion=self.on_motion)

    def on_model_path(self, instance, value):
        self._setup_object()

    def _setup_object(self):

        self.clear_widgets()
        if is_ios():  # TODO enable this when iOS bug is resolved
            self.add_widget(Label(text='3D render currently disabled\nfor iOS', halign='center'))
            return

        shader_file = resource_find(os.path.join('resource', 'models', 'shaders.glsl'))
        obj_path = resource_find(self.model_path)

        self.renderer = Renderer(shader_file=shader_file)
        scene = Scene()
        camera = PerspectiveCamera(15, 1, 1, 1000)
        loader = OBJLoader()
        obj = loader.load(obj_path)

        scene.add(*obj.children)
        for obj in scene.children:
            obj.pos.x = self.position_x
            obj.pos.y = self.position_y
            obj.pos.z = self.position_z
            obj.rotation.x = self.rotation_x
            obj.rotation.y = self.rotation_y
            obj.rotation.z = self.rotation_z
            obj.material.specular = .85, .85, .85
            obj.material.color = 1.0, 1.0, 1.0
            obj.material.diffuse = 0.5, 0.5, 0.5
            obj.material.transparency = 1.0
            obj.material.intensity = 0.5
            self.imu_obj = obj
            # obj.material.shininess = 1.0

        self.renderer.render(scene, camera)
        self.renderer.bind(size=self._adjust_aspect)
        Clock.schedule_once(lambda dt: self.add_widget(self.renderer))


    def _adjust_aspect(self, instance, value):
        rsize = self.renderer.size
        width = max(1, rsize[0])
        height = max(1, rsize[1])
        if height == 0:
            return
        self.renderer.camera.aspect = width / float(height)
        self.size_scaling = 1 / float(dp(1))  # width /  (width * height) / (Window.size[0] * Window.size[1])

    @property
    def _zoom_scaling(self):
        return self.size_scaling * ImuView.ZOOM_SCALING

    def define_rotate_angle(self, touch):
        x_angle = (touch.dx / self.width) * 360
        y_angle = -1 * (touch.dy / self.height) * 360
        return x_angle, y_angle

    def on_touch_down(self, touch):
        super(ImuView, self).on_touch_down(touch)
        if self._last_button == 'left' or self._last_button == None:
            self._total_drag_distance = 0

        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            touch.grab(self)
            self._touches.append(touch)
            return True
        return False

    def on_touch_up(self, touch):
        super(ImuView, self).on_touch_up(touch)
        x, y = touch.x, touch.y

        # remove it from our saved touches
        if touch in self._touches:  # and touch.grab_state:
            touch.ungrab(self)
            self._touches.remove(touch)

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            if self._total_drag_distance < ImuView.DRAG_CUSTOMIZE_THRESHOLD:
                self.dispatch('on_customize')
                self._total_drag_distance = ImuView.DRAG_CUSTOMIZE_THRESHOLD

            return True

        return False

    def on_touch_move(self, touch):
        Logger.debug("dx: %s, dy: %s. Widget: (%s, %s)" % (touch.dx, touch.dy, self.width, self.height))
        self._total_drag_distance += abs(touch.dx) + abs(touch.dy)

        if touch in self._touches and touch.grab_current == self:
            if len(self._touches) == 1:
                # here do just rotation
                ax, ay = self.define_rotate_angle(touch)

                self.rotation_x -= (ay * ImuView.ROTATION_SCALING)
                self.rotation_y += (ax * ImuView.ROTATION_SCALING)

                # ax, ay = math.radians(ax), math.radians(ay)

            elif len(self._touches) == 2:  # scaling here
                # use two touches to determine do we need scal
                touch1, touch2 = self._touches
                old_pos1 = (touch1.x - touch1.dx, touch1.y - touch1.dy)
                old_pos2 = (touch2.x - touch2.dx, touch2.y - touch2.dy)

                old_dx = old_pos1[0] - old_pos2[0]
                old_dy = old_pos1[1] - old_pos2[1]

                old_distance = (old_dx * old_dx + old_dy * old_dy)

                new_dx = touch1.x - touch2.x
                new_dy = touch1.y - touch2.y

                new_distance = (new_dx * new_dx + new_dy * new_dy)

                if new_distance > old_distance:
                    scale = 1 * self._zoom_scaling
                elif new_distance == old_distance:
                    scale = 0
                else:
                    scale = -1 * self._zoom_scaling

                if scale:
                    self.position_z += scale

    def on_motion(self, instance, event, motion_event):

        if motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            try:
                button = motion_event.button
                self._last_button = button
                SCALE_FACTOR = 0.1
                z_distance = self._zoom_scaling * ImuView.TOUCHWHEEL_ZOOM_MULTIPLIER
                if button == 'scrollup':
                    self.position_z += z_distance
                    self._total_drag_distance += 100
                else:
                    if button == 'scrolldown':
                        self.position_z -= z_distance
            except:
                pass  # no scrollwheel support


    def on_position_x(self, instance, value):
        try:
            self.imu_obj.pos.x = value
        except AttributeError:
            pass

    def on_position_y(self, instance, value):
        try:
            self.imu_obj.pos.y = value
        except AttributeError:
            pass

    def on_position_z(self, instance, value):
        try:
            self.imu_obj.pos.z = value
        except AttributeError:
            pass

    def on_rotation_x(self, instance, value):
        try:
            self.imu_obj.rotation.x = value
        except AttributeError:
            pass

    def on_rotation_y(self, instance, value):
        try:
            self.imu_obj.rotation.y = value
        except AttributeError:
            pass

    def on_rotation_z(self, instance, value):
        try:
            self.imu_obj.rotation.z = value
        except AttributeError:
            pass

    def on_accel_x(self, instance, value):
        try:
            self.imu_obj.pos.z = self.position_z + (value * ImuView.ACCEL_SCALING)
        except AttributeError:
            pass

    def on_accel_y(self, instance, value):
        try:
            self.imu_obj.pos.x = self.position_x - (value * ImuView.ACCEL_SCALING)
        except AttributeError:
            pass

    def on_accel_z(self, instance, value):
        try:
            # subtract 1.0 to compensate for gravity
            self.imu_obj.pos.y = self.position_y + ((value - 1.0) * ImuView.ACCEL_SCALING)
        except AttributeError:
            pass

    def on_gyro_yaw(self, instance, value):
        try:
            self.imu_obj.rotation.y = self.rotation_y - (value * ImuView.GYRO_SCALING)
        except AttributeError:
            pass

    def on_gyro_pitch(self, instance, value):
        try:
            self.imu_obj.rotation.x = self.rotation_x - (value * ImuView.GYRO_SCALING)
        except AttributeError:
            pass

    def on_gyro_roll(self, instance, value):
        try:
            self.imu_obj.rotation.z = self.rotation_z + (value * ImuView.GYRO_SCALING)
        except AttributeError:
            pass

