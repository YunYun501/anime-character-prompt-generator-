import {Fragment,useCallback,useContext,useEffect} from "react"
import {Box as RadixThemesBox,Button as RadixThemesButton,Flex as RadixThemesFlex,Heading as RadixThemesHeading,Text as RadixThemesText,TextArea as RadixThemesTextArea} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {ReflexEvent} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {jsx} from "@emotion/react"




function Debounceinput_75e44539c5c33976cb5cb436d4d65882 () {
  const reflex___state____state__reflex_generator___reflex_generator____app_state = useContext(StateContexts.reflex___state____state__reflex_generator___reflex_generator____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_change_260b75e9212be36d78c65fa88f01d55d = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_generator___reflex_generator____app_state.set_prompt", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(DebounceInput,{css:({ ["width"] : "100%" }),debounceTimeout:300,element:RadixThemesTextArea,onChange:on_change_260b75e9212be36d78c65fa88f01d55d,rows:"4",value:reflex___state____state__reflex_generator___reflex_generator____app_state.generated_prompt_rx_state_},)
  )
}


function Button_45ec49629657b915d3a742055a0d3c6b () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_ae129ae59d622192f556a70887c47162 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_generator___reflex_generator____app_state.generate_prompt", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"blue",onClick:on_click_ae129ae59d622192f556a70887c47162},"\u2728 Generate")
  )
}


function Button_1e02a727b59ee744688c79a1258e492f () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_d39e3e1daa48c44e95595eb9bc7de9c5 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_generator___reflex_generator____app_state.randomize_all", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{color:"green",onClick:on_click_d39e3e1daa48c44e95595eb9bc7de9c5},"\ud83c\udfb2 Randomize All")
  )
}


function Button_436fcae9123e60bafcf4f4b732e23f37 () {
  const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_99aed3b4e7bceebbae551c804d336eb8 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.reflex_generator___reflex_generator____app_state.reset_all", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])

  return (
    jsx(RadixThemesButton,{onClick:on_click_99aed3b4e7bceebbae551c804d336eb8},"\ud83d\udd04 Reset")
  )
}


function Button_bfb033deefd0b845b8a413b52e4be953 () {
  const reflex___state____state__reflex_generator___reflex_generator____app_state = useContext(StateContexts.reflex___state____state__reflex_generator___reflex_generator____app_state)
const [addEvents, connectErrors] = useContext(EventLoopContext);

const on_click_cfd056010daffb0736dadc3ff2ec9f1e = useCallback(((_e) => (addEvents([(ReflexEvent("_call_function", ({ ["function"] : (() => (navigator?.["clipboard"]?.["writeText"](reflex___state____state__reflex_generator___reflex_generator____app_state.generated_prompt_rx_state_))), ["callback"] : null }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent, reflex___state____state__reflex_generator___reflex_generator____app_state])

  return (
    jsx(RadixThemesButton,{onClick:on_click_cfd056010daffb0736dadc3ff2ec9f1e},"\ud83d\udccb Copy")
  )
}


function Box_ad200d1ab06bb6e4959d34adab300b8b () {
  
                useEffect(() => {
                    ((...args) => (addEvents([(ReflexEvent("reflex___state____state.reflex_generator___reflex_generator____app_state.initialize", ({  }), ({  })))], args, ({  }))))()
                    return () => {
                        
                    }
                }, []);
const [addEvents, connectErrors] = useContext(EventLoopContext);



  return (
    jsx(RadixThemesBox,{css:({ ["padding"] : "20px", ["maxWidth"] : "1200px", ["margin"] : "0 auto" })},jsx(RadixThemesHeading,{size:"7"},"\ud83c\udfa8 Random Anime Character Prompt Generator"),jsx(RadixThemesBox,{css:({ ["padding"] : "15px", ["border"] : "1px solid #e5e7eb", ["borderRadius"] : "8px", ["marginBottom"] : "15px" })},jsx(RadixThemesHeading,{size:"5"},"Generated Prompt"),jsx(Debounceinput_75e44539c5c33976cb5cb436d4d65882,{},),jsx(RadixThemesFlex,{align:"start",className:"rx-Stack",direction:"row",gap:"3"},jsx(Button_45ec49629657b915d3a742055a0d3c6b,{},),jsx(Button_1e02a727b59ee744688c79a1258e492f,{},),jsx(Button_436fcae9123e60bafcf4f4b732e23f37,{},),jsx(Button_bfb033deefd0b845b8a413b52e4be953,{},))),jsx(RadixThemesBox,{css:({ ["padding"] : "10px", ["background"] : "#f5f5f5", ["borderRadius"] : "4px" })},jsx(RadixThemesText,{as:"p"},"Slots: hair_style, hair_length, hair_color, hair_texture, eye_color, eye_style... (total: 26)")))
  )
}


export default function Component() {





  return (
    jsx(Fragment,{},jsx(Box_ad200d1ab06bb6e4959d34adab300b8b,{},),jsx("title",{},"Character Prompt Generator"),jsx("meta",{content:"favicon.ico",property:"og:image"},))
  )
}