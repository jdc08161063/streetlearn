# Copyright 2018 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Basic human agent for StreetLearn."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags

import time
import numpy as np
import pygame

from streetlearn.python.environment import courier_game
from streetlearn.python.environment import default_config
from streetlearn.python.environment import streetlearn

FLAGS = flags.FLAGS
flags.DEFINE_integer("width", 400, "Observation and map width.")
flags.DEFINE_integer("height", 400, "Observation and map height.")
flags.DEFINE_float("horizontal_rot", 10, "Horizontal rotation step (deg).")
flags.DEFINE_float("vertical_rot", 10, "Vertical rotation step (deg).")
flags.DEFINE_string("dataset_path", None, "Dataset path.")
flags.DEFINE_string("start_pano", "",
                     "Pano at root of partial graph (default: full graph).")
flags.DEFINE_integer("graph_depth", 200, "Depth of the pano graph.")
flags.DEFINE_integer("frame_cap", 1000, "Number of frames / episode.")
flags.DEFINE_float("proportion_of_panos_with_coins", 0.5, "Proportion of coins.")
flags.mark_flag_as_required("dataset_path")


HEIGHT_LINE = 30


def interleave(array, w, h):
  """Turn a planar RGB array into an interleaved one.

  Args:
    array: An array of bytes consisting the planar RGB image.
    w: Width of the image.
    h: Height of the image.
  Returns:
    An interleaved array of bytes shape shaped (h, w, 3).
  """
  arr = array.reshape(3, w * h)
  return np.ravel((arr[0], arr[1], arr[2]),
                  order='F').reshape(h, w, 3).swapaxes(0, 1)

def loop(env, screen):
  """Main loop of the human agent."""
  while True:
    pano_id = env.current_pano_id
    observation = env.observation()
    view_image = interleave(observation["view_image"],
                            FLAGS.width, FLAGS.height)
    graph_image = interleave(observation["graph_image"],
                             FLAGS.width, FLAGS.height)
    screen_buffer = np.concatenate((view_image, graph_image), axis=1)
    pygame.surfarray.blit_array(screen, screen_buffer)

    pygame.display.update()
    action_spec = env.action_spec()
    action = np.array([0, 0, 0, 0])

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        return
      elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          print(pano_id + ": exit")
          return
        if event.key == pygame.K_SPACE:
          action = action_spec["move_forward"]
          print(pano_id + ": move")
        elif event.key == pygame.K_p:
          filename = time.strftime('human_agent_%Y%m%d_%H%M%S.bmp')
          pygame.image.save(screen, filename)
        elif event.key == pygame.K_i:
          action = action_spec["map_zoom"]
          print(pano_id + ": zoom in")
        elif event.key == pygame.K_o:
          action = -1 * action_spec["map_zoom"]
          print(pano_id + ": zoom out")
        elif event.key == pygame.K_a:
          action = -FLAGS.horizontal_rot * action_spec["horizontal_rotation"]
          print(pano_id + ": rotate left")
        elif event.key == pygame.K_d:
          action = FLAGS.horizontal_rot * action_spec["horizontal_rotation"]
          print(pano_id + ": rotate right")
        elif event.key == pygame.K_w:
          action = -FLAGS.vertical_rot * action_spec["vertical_rotation"]
          print(pano_id + ": look up")
        elif event.key == pygame.K_s:
          action = FLAGS.vertical_rot * action_spec["vertical_rotation"]
          print(pano_id + ": look down")
      elif event.type == pygame.KEYUP:
        pass
    _, reward, _, _ = env.step(action)
    if reward > 0:
      pano_id = env.current_pano_id
      print("Collected reward of {} at {}".format(reward, pano_id))

def main(argv):
  config = {'width': FLAGS.width,
            'height': FLAGS.height,
            'graph_width': FLAGS.width,
            'graph_height': FLAGS.height,
            'graph_zoom': 1,
            'goal_timeout': FLAGS.frame_cap,
            'frame_cap': FLAGS.frame_cap,
            'full_graph': (FLAGS.start_pano == ""),
            'start_pano': FLAGS.start_pano,
            'min_graph_depth': FLAGS.graph_depth,
            'max_graph_depth': FLAGS.graph_depth,
            'proportion_of_panos_with_coins':
                FLAGS.proportion_of_panos_with_coins,
            'observations': ['view_image', 'graph_image', 'yaw', 'pitch',
                             'latlng', 'target_latlng']}
  config = default_config.ApplyDefaults(config)
  game = courier_game.CourierGame(config)
  env = streetlearn.StreetLearn(FLAGS.dataset_path, config, game)
  env.reset()
  pygame.init()
  screen = pygame.display.set_mode((FLAGS.width, FLAGS.height * 2))
  loop(env, screen)

if __name__ == '__main__':
  app.run(main)
