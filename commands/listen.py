import lldb
import fbchisellldbbase as fb
from typing import cast
from typing_extensions import override
import threading

debugger = cast(lldb.SBDebugger, lldb.debugger)



def lldbcommands():
    return [ListenModuleWithOffset()]


class ListenModuleWithOffset(fb.FBCommand):
    @override
    def name(self) -> str:  # type: ignore
        return "lmo"

    @override
    def description(self) -> str:  # type: ignore
        return "listen module load and set breakpoint with offset"

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="viewOrLayer",
                type="UIView/NSView/CALayer *",
                help="The view/layer to border. NSViews must be layer-backed.",
            ),
            fb.FBCommandArgument(
                arg="offset",
                type="string",
                help="the offset with hex format",
            ),
        ]

    def run(self, arguments, option):
        target: lldb.SBTarget = lldb.debugger.GetSelectedTarget()  # type: lldb.SBTarget
        broadcaster: lldb.SBBroadcaster = target.GetBroadcaster()
        # Create an empty event object.
        event = lldb.SBEvent()
        listener = lldb.SBListener("my listener")
        broadcaster.AddListener(listener, lldb.SBTarget.eBroadcastBitModulesLoaded)
        traceOn = True

        class MyListeningThread(threading.Thread):
            def run(self):
                count = 0
                # Let's only try at most 4 times to retrieve any kind of event.
                # After that, the thread exits.
                while True:
                    if traceOn:
                        print("Try wait for event...")
                    if listener.WaitForEventForBroadcasterWithType(
                        5, broadcaster, lldb.SBTarget.eBroadcastBitModulesLoaded, event
                    ):
                        if traceOn:
                            num_modules = lldb.SBTarget.GetNumModulesFromEvent(event)
                            for i in range(num_modules):
                                module = lldb.SBTarget.GetModuleAtIndexFromEvent(
                                    event, i
                                )
                                print(f"加载模块: {module.GetFileSpec()}")
                            # print('Event description:', desc)
                            # print('Event data flavor:', event.GetDataFlavor())
                            # print('Process state:', lldbutil.state_type_to_str(process.GetState()))
                            # print()
                    else:
                        if traceOn:
                            print("timeout occurred waiting for event...")
                    count = count + 1
                return

        my_thread = MyListeningThread()
        my_thread.start()
        my_thread.join()
