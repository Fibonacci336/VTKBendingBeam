import vtk
import numpy as np
from PyQt5 import QtWidgets, QtCore
import Settings


class MouseKeyboardInteractor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self, main_window, parent=None):
        self.AddObserver("LeftButtonPressEvent", self.left_button_pressed)
        self.AddObserver("KeyPressEvent", self.key_pressed)
        self.main_window = main_window
        self.last_picked_actor = None
        self.new_actor = None
        self.last_picked_property = vtk.vtkProperty()



    def key_pressed(self, renderer, event):
        key = self.GetInteractor().GetKeySym()
        azi_step = 2
        ele_step = 2
        yaw_step = 0.5
        camera = self.main_window.active_camera
        if self.GetInteractor().GetShiftKey():
            if key == "Left":
                camera.Roll(-azi_step)
            if key == "Right":
                camera.Roll(azi_step)
            if key == "Up":
                camera.Elevation(ele_step)
            if key == "Down":
                camera.Elevation(-ele_step)
        else:
            if key == "Left":
                camera.Yaw(yaw_step)
            if key == "Right":
                camera.Yaw(-yaw_step)
            if key == "Up":
                print(camera.GetOrientationWXYZ())
                #Settings.camera.Elevation(ele_step)
            #if key == "Down":
                #Settings.camera.Elevation(-ele_step)

    def left_button_pressed(self, obj, event):

        click_pos = self.GetInteractor().GetEventPosition()

        picker = vtk.vtkPropPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, self.GetDefaultRenderer())

        # get the new actor
        self.new_actor = picker.GetActor()

        # If something was selected
        if self.new_actor:
            # If we picked something before, reset its property
            if self.last_picked_actor:
                self.last_picked_actor.GetProperty().DeepCopy(self.last_picked_property)

            # Save the property of the picked actor so that we can
            # restore it next time
            self.last_picked_property.DeepCopy(self.new_actor.GetProperty())

            # Allows selection only for nodes
            producer = self.new_actor.GetMapper().GetInputConnection(0, 0).GetProducer()
            if type(producer) is not vtk.vtkSphereSource:
                return

            # Highlight the picked actor by changing its properties
            self.new_actor.GetProperty().SetColor(0.0, 0.0, 1.0)
            self.new_actor.GetProperty().SetDiffuse(1.0)
            self.new_actor.GetProperty().SetSpecular(0.0)

            selected_x = self.new_actor.GetCenter()[0]

            if Settings.attach_camera_to_node and not Settings.camera_is_attached:
                Settings.selecting_camera_index += 1
                if Settings.selecting_camera_index == 1:
                    # Adding Position Point
                    Settings.cam_pos_index = selected_x
                    Settings.positionActor = self.new_actor
                    self.main_window.attach_cam_label.setText("Click node to set focal point")
                    return

                if Settings.selecting_camera_index == 2:
                    # Adding Focal Point
                    if selected_x == Settings.cam_pos_index:
                        msg_box = QtWidgets.QMessageBox()
                        msg_box.setText("Can not select focal point at position node!")
                        msg_box.setIcon(QtWidgets.QMessageBox.Information)
                        msg_box.setWindowTitle("Error!")
                        msg_box.setStandardButtons(QtWidgets.QMessageBox.Cancel)
                        msg_box.exec()

                        Settings.selecting_camera_index -= 1
                        return

                    Settings.cam_focal_index = selected_x
                    Settings.focalActor = self.new_actor

                    Settings.update_slot.set_camera_indicies(Settings.cam_pos_index, Settings.cam_focal_index)
                    self.main_window.attach_cam_label.setText("")

                pos_center = Settings.positionActor.GetCenter()
                focal_center = Settings.focalActor.GetCenter()
                camera = self.main_window.active_camera

                Settings.selecting_camera_index = 0
                Settings.camera_is_attached = True
                camera.SetPosition(np.add(pos_center, Settings.camera_delta_values))
                camera.SetFocalPoint(focal_center)
                Settings.vtk_widget.GetRenderWindow().Render()
                return

            actor_center = self.new_actor.GetCenter()
            actor_x = actor_center[0]
            actor_y = actor_center[1]
            actor_z = actor_center[2]

            msg_box = QtWidgets.QMessageBox()
            msg_box.setText("X: {}\nY: {}\nZ: {}".format(actor_x, actor_y, actor_z))

            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Node Info")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Cancel)

            returnValue = msg_box.exec()

            # save the last picked actor
            self.last_picked_actor = self.new_actor

        self.OnLeftButtonDown()
        return
