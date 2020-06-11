Samples Library
===============

Library of samples in original Ogzi format. See [Releases](https://github.com/ogzi-music/lib/releases).

Ogzi Sample Format
==================

The sample library is a simple XZipped TAR package consisting:

* Simple description in YAML format.
* Directory with audio files in FLAC format.

Ogzi YAML Fields
----------------

* `name`: Human readable library name.
* `id`: Internal name, should be the same as the audio files directory name.
* `samples`: Array of sample descriptions:

    - `file`: Audio file name.
    - `key`: Assigned key number (see [Key Number](#key-number)).
    - `key-from` (_optional_): Left key number in a range covered by this sample (see [Key Number](#key-number)). Equals to `key` if missing.
    - `key-to` (_optional_): Right key number in a range covered by this sample (see [Key Number](#key-number)). Equals to `key` if missing.
    - `velocity-from` (_optional_): Minimum velocity covered by this sample. Equals to `1` if missing.
    - `velocity-to` (_optional_): Maximum velocity covered by this sample. Equals to `127` if missing.
    - `level`: Volume level, from `1` to `127`.
    - `pan` (_optional_): Stereo panning, `64` for the central value, less than `64` to the left channel, more than `64` to the right channel. Equals to `64` if missing.
    - `tune-coarse` (_optional_): Coarse tuning parameter, less than `64` to the down side, more than `64` to the up side. Equals to `64` if missing.
    - `tune-fine` (_optional_): Fine tuning parameter, less than `64` to the down side, more than `64` to the up side. Equals to `64` if missing.
    - `channels`: Channel count, `1` for mono, `2` for stereo.
    - `bit-depth`: Audio bit depth.
    - `mode`: Playback mode. Options: `loop` for looped playback, `single-shot` for single time playback, `reverse` for reversed playback.
    - `frequency`: Sampling frequency in Hz.
    - `length`: Sample count in a waveform.
    - `start` (_optional_): Start point, from `0` to `length − 1`. Equals to `0` if missing.
    - `end` (_optional_): End point, from `0` to `length − 1`. Equals to `length − 1` if missing.
    - `loop` (_when_ `mode` = `loop` _only_): Loop start point, from `0` to `length − 1`.


Key Number
----------

The key number is the integer from 0 to 120. It can be translated to the human readable notation using the following equations:

* _Note_ = _Letter_[_Number_ **mod** _12_], where _Letter_ =  [_C_, _C#_, _D_, _D#_, _E_, '_F_, _F#_, _G_, _G#_, _A_, _A#_, _B_]
* _Octave_ = (_Number_ **div** _12_) − _2_

**mod** means the modulo operation, and **div** stands for the truncated division.

For example, `38` results in `D1`:

* _Note_ = _Letter_[_38_ **mod** 12 = _2_] → _D_
* _Octave_ = (_38_ **div** 12 = _3_) − _2_ → _1_

License
=======

All contents are licensed under [Creative Commons Zero v1.0 Universal License](LICENSE).