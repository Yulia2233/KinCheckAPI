"""Execute shipped browser handlers against a deterministic DOM/scene harness."""

from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize(
    "script", ["viewer/static/app.js", "src/kincheckapi/_viewer_static/app.js"]
)
def test_static_slider_selects_all_poses_and_legacy_ratio_has_unit(script):
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required to execute the viewer handlers")
    source = Path(__file__).resolve().parents[1] / script
    program = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
function definition(name) {
  const match = source.match(new RegExp('^function '+name+'\\([^]*?^}', 'm'));
  assert.ok(match, `Missing shipped handler ${name}`);
  return match[0];
}
const labels = new Map();
const dom = {querySelector(id) {
  if (!labels.has(id)) labels.set(id,{textContent:'',parentElement:{lastChild:{textContent:' s'}}});
  return labels.get(id);
}};
const received=[];
const object={position:{fromArray(v){object.position.value=v;}},quaternion:{fromArray(v){object.quaternion.value=v;}}};
const cases=[0,1,2].map(i=>({component_poses:{arm:{position_m:[i,0,0],orientation_xyzw:[0,0,i/10,1]}}}));
const context=vm.createContext({
  manifest:{physics_case_count:3,physics:{static_results:cases},sample_count:1,
    start_time_s:5,end_time_s:5,components:[{component_id:'arm'}]},
  document:dom,componentObjects:new Map([['arm',object]]),timeline:{value:'0'},
  currentCaseIndex:0,currentTime:5,updatePhysics(i){received.push(i);},
  setPlaying(){},Math,
});
vm.runInContext(['physicsCaseCount','updateStaticCase','updateTime','expectedRatioLabel'].map(definition).join('\n'),context);
const slider=source.match(/timeline\.addEventListener\("input", \(\) => \{([^]*?)\n\}\);/);
assert.ok(slider,'Use the actual browser slider handler');
for (const [fraction,index] of [[0,0],[0.5,1],[1,2]]) {
  context.timeline.value=String(fraction);
  vm.runInContext(slider[1],context);
  assert.equal(received.at(-1),index);
  assert.deepEqual(object.position.value,[index,0,0]);
  assert.deepEqual(object.quaternion.value,[0,0,index/10,1]);
  assert.equal(labels.get('#sample-readout').textContent,`Static case ${index+1} / 3`);
}
assert.equal(context.currentTime,5,'Static case selection must not rewrite physical time');
assert.equal(vm.runInContext('expectedRatioLabel({expected_ratio:2})',context),'2.000:1');
assert.equal(vm.runInContext('expectedRatioLabel({expected_ratio:2,ratio_unit:"m/rad"})',context),'2.000 m/rad');
// Old manifests lacking the new count still use their actual static cases.
delete context.manifest.physics_case_count;
assert.equal(vm.runInContext('physicsCaseCount()',context),3);
"""
    result = subprocess.run(
        [node, "-e", program, str(source)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
